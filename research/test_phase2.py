import copy
from pathlib import Path

import pytest

from gnome_fortress import engine
from gnome_fortress.engine import World
from gnome_fortress.model import Cell
from research.phase2_controls import (CAPACITIES, BlindReadout, Config, ExperimentalWorld,
                                     biological_digest, capacity, load_experiment, save_experiment)


@pytest.mark.parametrize("seed", [1, 1001])
def test_enabled_is_exact_baseline(seed):
    a, b = World(seed), ExperimentalWorld(seed)
    a.step(500)
    b.step(500)
    assert a.state() == b.state()


def test_readout_mask_preserves_learning():
    w = ExperimentalWorld(8, Config(memory="ablated"))
    a = w.agents[1]
    a.learned["move:hazard"] = -40
    original = a.learned
    a.learned = BlindReadout(original)
    assert a.learned.get("move:hazard") == 0
    w.remember(a, "move", "hazard", -80)
    assert dict.get(a.learned, "move:hazard") == -50  # Actual prior, not masked zero.
    assert a.learned.get("move:hazard") == 0
    assert a.memories[-1].reward == -80
    assert a.learned.blind


def test_ablated_choice_only_changes_associative_readout():
    w = ExperimentalWorld(1, Config(memory="ablated"))
    for row in w.cells:
        for cell in row:
            cell.terrain, cell.food = "rock", 0
    for a in w.agents.values():
        a.x = a.y = 1
    a = w.agents[1]
    a.x = a.y = 4
    a.hunger = a.thirst = 0
    a.traits["caution"] = 0
    a.learned["move:hazard"] = -100
    w.cells[4][4] = Cell("grass")
    w.cells[3][4] = Cell("hazard")
    w.cells[4][5] = Cell("grass")
    control = World.from_state(copy.deepcopy(w.state()))
    control.agents[1].learned["move:hazard"] = 0
    w.move(a)
    control.move(control.agents[1])
    b = control.agents[1]
    assert (a.x,a.y) == (b.x,b.y)
    assert w.rng.getstate() == control.rng.getstate()
    assert a.traits == b.traits and a.visits == b.visits
    assert isinstance(a.learned, dict) and not isinstance(a.learned, BlindReadout)


def test_capacity_context_restores_on_failure():
    with pytest.raises(RuntimeError):
        with capacity(960):
            assert engine.SLOTS == 960
            raise RuntimeError("test")
    assert engine.SLOTS == 60
    with pytest.raises(ValueError):
        Config(slots=61)


@pytest.mark.parametrize("slots", CAPACITIES)
@pytest.mark.parametrize("memory", ["enabled", "ablated"])
def test_capacity_replay_and_persistence(tmp_path, slots, memory):
    cfg = Config(slots, memory)
    with capacity(slots):
        a, b = ExperimentalWorld(4, cfg), ExperimentalWorld(4, cfg)
        # Oversubscribe all tested capacities without changing main-campaign starts.
        for w in (a,b):
            for _ in range(slots+10):
                w._spawn(1,1,w.agents[1].traits,(1,2))
        a.step(20)
        b.step(20)
        assert a.state() == b.state()
        a.validate()
        path=tmp_path / "checkpoint.sqlite"
        save_experiment(a, path)
        restored=load_experiment(path, cfg)
        assert restored.state() == a.state()
        a.step(5)
        restored.step(5)
        assert a.digest() == restored.digest()
        with pytest.raises(ValueError):
            load_experiment(path, Config(slots, "ablated" if memory == "enabled" else "enabled"))
    assert engine.SLOTS == 60


def test_initial_biology_equal_for_all_capacities():
    digests=[]
    for slots in CAPACITIES:
        with capacity(slots):
            digests.append(biological_digest(ExperimentalWorld(8,Config(slots))))
    assert len(set(digests)) == 1


def test_hazard_death_counter_does_not_duplicate_encounter():
    from collections import Counter
    from gnome_fortress.model import Event
    from research.phase2_run import count_event
    c=Counter()
    count_event(c,Event(1,"hazard",1,None,{"damage":30}))
    count_event(c,Event(1,"death",1,None,{"cause":"hazard"}))
    assert c["hazard"]==1 and c["death"]==1 and c["cause:hazard"]==1


def test_no_association_signal_means_no_treatment_difference():
    a=ExperimentalWorld(42,Config(memory='enabled'))
    b=ExperimentalWorld(42,Config(memory='ablated'))
    for w in (a,b):
        for row in w.cells:
            for cell in row:
                if cell.terrain=='hazard':
                    cell.terrain='grass'
    a.step(100)
    b.step(100)
    assert a.state()==b.state()


def test_paired_interval_retains_constant_pair_effect():
    import numpy as np
    from research.phase2_analyze import paired_effect
    samples=np.random.default_rng(1).integers(0,3,size=(1000,3))
    result=paired_effect([2,4,6],[1,3,5],samples)
    assert result['mean_paired_difference']==1
    assert result['bootstrap_95_low']==result['bootstrap_95_high']==1
    assert result['paired_t_95_low']==result['paired_t_95_high']==1
