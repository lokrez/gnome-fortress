import copy
import random

import pytest

from gnome_fortress.engine import SLOTS, World
from gnome_fortress.model import Cell
from gnome_fortress.storage import load, save


@pytest.mark.parametrize("seed", [1, 42, 2026])
def test_deterministic_replay(seed):
    left, right = World(seed), World(seed)
    left.step(450)
    for _ in range(450):
        right.step()
    assert left.state() == right.state()
    assert left.digest() == right.digest()
    assert len(World(seed).agents) == 60
    assert len({a.name for a in World(seed).agents.values()}) == 60
    assert World(seed + 1).digest() != World(seed).digest()


def test_no_global_random_dependency():
    a, b = World(8), World(8)
    for _ in range(30):
        random.random()
        a.step()
        random.seed(22)
        b.step()
    assert a.digest() == b.digest()


@pytest.mark.parametrize("checkpoint_tick", [0, 91, 500])
def test_checkpoint_continuation(tmp_path, checkpoint_tick):
    a = World(42)
    a.step(checkpoint_tick)
    path = tmp_path / "world.sqlite"
    save(a, path)
    b = load(path)
    assert a.state() == b.state()
    a.step(300)
    b.step(300)
    assert a.digest() == b.digest()
    # A second checkpoint replaces rather than duplicates history.
    save(b, path)
    assert load(path).state() == b.state()


def test_death_is_permanent():
    w = World(4)
    a = w.agents[1]
    w.kill(a, "test")
    death_tick = a.died
    w.kill(a, "again")
    w.step(500)
    assert a.id in w.agents and not a.alive and a.died == death_tick
    assert a.id not in w.slots
    assert sum(e.kind == "death" and e.actor == a.id for e in w.events) == 1
    w.validate()


def test_old_age_and_need_deaths():
    w = World(4)
    old = w.agents[1]
    old.age = 1800 + old.traits["stamina"] * 12 - 1
    thirsty = w.agents[2]
    thirsty.thirst, thirsty.health = 120, 1
    w.step()
    assert old.death_cause == "old_age"
    assert thirsty.death_cause == "dehydration"


def test_reproduction_ancestry_and_accounting():
    w = World(1)
    w.step(3000)
    w.validate()
    assert len(w.agents) > 60
    assert len(w.living()) + sum(not a.alive for a in w.agents.values()) == len(w.agents)
    assert any(e.kind == "death" for e in w.events)
    assert any(e.kind == "social" for e in w.events)
    assert any(e.kind == "hazard" for e in w.events)
    for a in w.agents.values():
        if a.parents:
            assert len(a.parents) == 2 and all(p < a.id for p in a.parents)
            for k, v in a.traits.items():
                mean = sum(w.agents[p].traits[k] for p in a.parents) // 2
                assert abs(v - mean) <= 10
            reproduction = next(e for e in w.events if e.kind == "reproduce" and e.detail["child"] == a.id)
            assert set(a.parents) == {reproduction.actor, reproduction.target}


def test_sleep_relinquishes_and_wake_restores_memories():
    w = World(1)
    a = w.agents[1]
    a.hunger = a.thirst = 0
    a.fatigue = 80
    w.remember(a, "move", "hazard", -80)
    memories = copy.deepcopy(a.memories)
    w.decide(a)
    assert a.action == "sleep"
    assert a.id not in w.schedule()
    a.health = 100
    until = a.sleep_until
    for _ in range(until - 1):
        w.step()
        assert a.id not in w.slots
        assert a.memories == memories
    w.step()
    assert a.sleep_until <= w.tick and a.id in w.slots
    assert a.memories[:1] == memories
    assert any(e.kind == "wake" and e.actor == a.id for e in w.events)
    assert a.age > 0  # sleeping never stops the biological clock


def test_urgent_need_wakes_early():
    w = World()
    a = w.agents[1]
    a.sleep_until, a.thirst = 20, 84
    w.step()
    assert a.sleep_until == 1
    assert a.id in w.slots


def test_waterfall_fairness_and_unique_assignments():
    w = World()
    for _ in range(85):
        w._spawn(1, 1, w.agents[1].traits, (1, 2))
    w.agents[3].sleep_until = 100
    w.kill(w.agents[4], "test")
    seen = set()
    for _ in range(3):
        assignments = w.schedule()
        assert len(assignments) == SLOTS
        assert len(set(assignments)) == SLOTS
        assert 3 not in assignments and 4 not in assignments
        seen.update(assignments)
    assert seen == {a.id for a in w.living() if a.id != 3}
    w.agents[3].sleep_until = 0
    seen = set(w.schedule()) | set(w.schedule()) | set(w.schedule())
    assert 3 in seen
    w.validate()


def test_birth_joins_on_following_schedule():
    w = World()
    w.schedule()
    child = w._spawn(1, 1, w.agents[1].traits, (1, 2))
    assert child.id not in w.slots
    assert child.id in w.schedule()


def test_hazard_experience_changes_decision_measurably():
    # Paired intervention: same world, traits, needs, visit counts and RNG;
    # erase only the learned association in the control branch.
    trained_hazards = control_hazards = 0
    for seed in range(100):
        w = World(seed, 8, 8)
        for row in w.cells:
            for c in row:
                c.terrain, c.food = "rock", 0
        for other in w.agents.values():
            other.x = other.y = 1  # No competing social incentive at the test cell.
        w.cells[1][1] = Cell("grass")
        a = w.agents[1]
        a.x = a.y = 4
        a.hunger = a.thirst = 0
        a.traits["caution"] = 0
        w.cells[4][4] = Cell("grass")
        w.cells[3][4] = Cell("hazard")
        w.move(a)  # Real encounter; hazard was the only possible move.
        assert a.learned["move:hazard"] < 0
        a.x = a.y = 4
        a.visits.clear()
        w.cells[4][5] = Cell("grass")
        control = World.from_state(copy.deepcopy(w.state()))
        control.agents[1].learned.clear()
        w.move(a)
        control.move(control.agents[1])
        trained_hazards += w.cell(a.x, a.y).terrain == "hazard"
        b = control.agents[1]
        control_hazards += control.cell(b.x, b.y).terrain == "hazard"
    assert trained_hazards == 0
    assert 30 <= control_hazards <= 70
    print(f"memory paired experiment: trained={trained_hazards}/100 hazard choices; erased={control_hazards}/100")


def test_directional_relationships():
    w = World(1)
    w.step(300)
    assert any(a.relationships for a in w.agents.values())
    assert any(value != w.agents[b].relationships.get(a.id, 0)
               for a in w.agents.values() for b, value in a.relationships.items())


def test_curiosity_changes_exploration_choice():
    w = World(1, 8, 8)
    for row in w.cells:
        for c in row:
            c.terrain, c.food = "rock", 0
    for other in w.agents.values():
        other.x = other.y = 1
    w.cells[1][1] = Cell("grass")
    a = w.agents[1]
    a.x = a.y = 4
    a.hunger, a.thirst = 10, 0
    a.visits = {"5,4": 1}
    a.traits["curiosity"] = 0
    w.cells[4][4] = Cell("grass")
    w.cells[3][4] = Cell("grass")
    w.cells[4][5] = Cell("grass", 50)
    curious = World.from_state(copy.deepcopy(w.state()))
    curious.agents[1].traits["curiosity"] = 100
    w.move(a)
    curious.move(curious.agents[1])
    assert (a.x, a.y) == (5, 4)
    assert (curious.agents[1].x, curious.agents[1].y) == (4, 3)
