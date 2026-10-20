import copy
import sqlite3

import pytest

from gnome_fortress.communication import (CommunicationConfig, CommunicationWorld,
                                          load_experiment, save_experiment)
from gnome_fortress.engine import World
from research.phase4a_experiment import behavioral_state, probe, two_gnomes


def test_disabled_has_exact_reference_engine_state():
    actual, reference = CommunicationWorld(42), World(42)
    for boundary in (0, 1, 50, 200):
        actual.step(boundary-actual.tick); reference.step(boundary-reference.tick)
        assert World.state(actual) == reference.state()
        assert len(actual.slots) == 60
    assert actual.messages == 0


def test_invalid_config_rejected():
    with pytest.raises(ValueError): CommunicationConfig('magic')


def test_matched_probe_transfer_and_sham_control():
    changes = []
    for seed in range(1, 65):
        rows, worlds = {}, {}
        for condition in ('individual', 'social', 'sham'):
            rows[condition], worlds[condition] = probe(seed, condition)
        assert behavioral_state(worlds['individual']) == behavioral_state(worlds['sham'])
        assert worlds['individual'].rng.getstate() == worlds['sham'].rng.getstate()
        heard = rows['social']['recipient_heard']
        if heard:
            assert rows['social']['recipient_firsthand'] == 0
            assert rows['social']['recipient_value'] < 0
            assert abs(rows['social']['recipient_value']) < abs(rows['social']['source_value'])
            assert rows['social']['recipient_hazard'] == 0
        if rows['individual']['recipient_hazard'] and heard:
            changes.append(seed)
            assert worlds['social'].agents[2].memories[-2].action == 'hear'
            assert not any(m.action == 'move' and m.feature == 'hazard'
                           for m in worlds['social'].agents[2].memories)
    assert changes, 'No demonstrated recipient movement change; do not verify experiment'


def test_local_awake_experienced_source_only_and_no_forwarding():
    world = two_gnomes(1, 'social')
    a, b = world.agents[1], world.agents[2]
    a.x = 20
    assert not world.contact(a, b)
    a.x = 4; b.sleep_until = 100
    assert not world.contact(a, b)
    b.sleep_until = 0
    assert world.contact(a, b)
    # Hearsay by itself is not an eligible source.
    child = world._spawn(3, 2, a.traits, (1, 2))
    assert not world.contact(b, child)
    assert not world.contact(b, a)
    assert world.origins[2]['move:hazard']['firsthand_count'] == 0
    world.remember(b, 'move', 'hazard', -60)
    assert not world.contact(a, b)  # firsthand recipient no longer accepts lessons
    assert world.origins[2]['move:hazard']['firsthand_count'] == 1


def test_repeated_messages_attenuated_and_memories_bounded():
    world = two_gnomes(1, 'social')
    a, b = world.agents[1], world.agents[2]
    for _ in range(100): assert world.contact(a, b)
    assert len(b.memories) == 64
    assert a.learned['move:hazard'] < b.learned['move:hazard'] < 0
    assert world.origins[2]['move:hazard']['social_count'] == 100


@pytest.mark.parametrize('condition', ['individual', 'social', 'sham'])
def test_replay_and_save_load_include_provenance(tmp_path, condition):
    world = two_gnomes(3, condition)
    path = tmp_path / 'experiment.sqlite'
    world.step()
    save_experiment(world, path)
    loaded = load_experiment(path)
    assert loaded.state() == world.state()
    world.step(20); loaded.step(20)
    assert loaded.state() == world.state()
    assert loaded.digest() == world.digest()
    assert loaded.rng.getstate() == world.rng.getstate()


def test_experiment_checkpoint_protects_baseline_and_detects_corruption(tmp_path):
    from gnome_fortress.storage import save
    standard = tmp_path / 'standard.sqlite'
    save(World(), standard)
    before = standard.read_bytes()
    with pytest.raises(ValueError, match='Refusing'): save_experiment(CommunicationWorld(), standard)
    assert standard.read_bytes() == before
    path = tmp_path / 'experimental.sqlite'
    save_experiment(CommunicationWorld(), path)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE communication_checkpoint SET state='{}'")
    with pytest.raises(ValueError, match='checksum'): load_experiment(path)


def test_natural_world_deterministic_with_communication_enabled():
    a = CommunicationWorld(4, CommunicationConfig('social'))
    b = CommunicationWorld(4, CommunicationConfig('social'))
    a.step(200); b.step(200)
    assert a.state() == b.state()
    a.validate()


def test_checkpoint_failed_update_rolls_back_atomically(tmp_path):
    path = tmp_path / 'experiment.sqlite'
    world = CommunicationWorld(2)
    save_experiment(world, path)
    previous = world.state()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER fail_write BEFORE INSERT ON communication_checkpoint BEGIN SELECT RAISE(ABORT,'injected'); END")
    world.step(2)
    with pytest.raises(sqlite3.IntegrityError): save_experiment(world, path)
    assert load_experiment(path).state() == previous


def test_descendant_inspector_records_provenance_without_changing_world():
    from gnome_fortress.observatory import Observation
    world = two_gnomes(3, 'social')
    child = world._spawn(3, 3, world.agents[2].traits, (1, 2))
    assert world.contact(world.agents[1], child)
    before = world.state()
    view = Observation(world)
    view.select_population('descendants')
    assert view.roster == (child.id,)
    text = '\n'.join(view.persona())
    assert f'ID {child.id}' in text and 'Parents: (1, 2)' in text
    assert 'KNOWLEDGE ORIGINS' in text
    assert '"firsthand_count": 0' in text and '"social_count": 1' in text
    assert 'communication actor=1' in text
    view.layout(80, 24); view.layout(30, 12)
    assert world.state() == before
    view.select_population('founders')
    assert view.roster == tuple(range(1, 61))
    view.select_population('descendants')
    world.kill(child, 'test')
    assert 'No living descendants' in '\n'.join(view.persona())
    assert view.layout(80, 24)


def test_descendant_roster_birth_death_and_selection():
    from gnome_fortress.observatory import Observation
    w = CommunicationWorld()
    view = Observation(w); view.select_population('descendants')
    assert not view.roster
    children = [w._spawn(1, 1, w.agents[1].traits, (1, 2)) for _ in range(3)]
    view.refresh_roster(); view.navigate(1)
    selected = view.roster[view.selected]
    w.kill(children[0], 'test')
    view.refresh_roster()
    assert view.roster[view.selected] == selected
    view.navigate(1)
    assert view.roster[view.selected] == children[2].id


def test_experimental_checkpoint_observatory_readonly(tmp_path):
    from gnome_fortress.observatory import load_snapshot, Observation
    world = two_gnomes(3, 'social'); world.step()
    path = tmp_path / 'experiment.sqlite'; save_experiment(world, path)
    before = path.read_bytes()
    loaded = load_snapshot(path, loader=load_experiment)
    view = Observation(loaded, live=False)
    for _ in range(3): view.layout(80, 24); view.toggle(); view.step()
    assert loaded.state() == world.state() and path.read_bytes() == before


def test_experimental_state_snapshot_owns_provenance():
    w = two_gnomes(1, 'social')
    data = w.state()
    saved = copy.deepcopy(data)
    restored = CommunicationWorld.from_state(data)
    restored.contact(restored.agents[1], restored.agents[2])
    w.contact(w.agents[1], w.agents[2])
    assert data == saved


def test_experimental_writer_rejects_uninstrumented_world(tmp_path):
    path = tmp_path / 'not-created.sqlite'
    with pytest.raises(TypeError): save_experiment(World(), path)
    assert not path.exists()
