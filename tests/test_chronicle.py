import pickle
from dataclasses import asdict
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.chronicle import Chronicle


def warm(c,w):
    for _ in range(10000):
        c.prepare(w,.01)
        if len(w.events)-c.prepared<128 and not c.dead_queue:return
    raise AssertionError('preparation did not complete')


def test_cache_detachment_and_mutation_invalidation():
    w=TerrainWorld();w.step(400);c=Chronicle();before=w.state();warm(c,w)
    assert w.state()==before
    blob=c.capture(w);assert pickle.loads(blob).state()==before
    w.events[0].detail['parents'].append(999)
    w.events[1].kind='edited'
    dead=next(a for a in w.agents.values() if not a.alive)
    dead.health=-12;dead.learned['test']=7;dead.memories[0].reward=27
    assert pickle.loads(c.capture(w)).state()==w.state()
    assert pickle.loads(blob).state()==before
    w.events[0]=w.events[1]
    assert pickle.loads(c.capture(w)).state()==w.state()


def test_cold_tail_rebind_and_rewind():
    c=Chronicle();w=TerrainWorld();w.step(100)
    assert pickle.loads(c.capture(w)).state()==w.state()
    warm(c,w);w.step(20)
    assert pickle.loads(c.capture(w)).state()==w.state()
    w.events=list(w.events);assert pickle.loads(c.capture(w)).state()==w.state()
    other=TerrainWorld(2);assert pickle.loads(c.capture(other)).state()==other.state()


def test_reference_and_prepared_simulation_equal():
    a=TerrainWorld(1);b=TerrainWorld(1);c=Chronicle()
    for tick in range(500):
        if tick in (10,20,30,40,50):
            for w in (a,b):w.request({10:'rain',20:'drought',30:'rupture',40:'rewild',50:'wellspring'}[tick],10,10)
        a.step();b.step();c.prepare(b,.001)
        if tick%50==0:assert pickle.loads(c.capture(b)).state()==a.state()
    assert a.state()==b.state()


def test_prepared_nested_container_mutations_and_replaced_dead():
    w=TerrainWorld();w.step(500);c=Chronicle();warm(c,w)
    e=w.events[0];e.detail.update(test={'nested':[1,2]});assert pickle.loads(c.capture(w)).state()==w.state()
    e.detail['test']['nested'][:]=[3];e.detail['test']['nested']+= [4]
    e.detail['test']['nested'].reverse();e.detail['test']['nested'].pop()
    assert pickle.loads(c.capture(w)).state()==w.state()
    dead=next(a for a in w.agents.values() if not a.alive)
    from gnome_fortress.model import Agent,Episode
    values=asdict(dead);values['memories']=[Episode(**m) for m in values['memories']]
    w.agents[dead.id]=Agent(**values);w.agents[dead.id].health-=1
    del dead
    assert pickle.loads(c.capture(w)).state()==w.state()
    w.events=w.events[::-1]
    assert pickle.loads(c.capture(w)).state()==w.state()


def test_explicit_invalidation_and_corrupted_cache_fail_closed():
    w=TerrainWorld();w.step(400);c=Chronicle();warm(c,w)
    c.blocks[0].payload=b'not a pickle'
    import pytest
    with pytest.raises(pickle.UnpicklingError):pickle.loads(c.capture(w))
    c.invalidate();warm(c,w);assert pickle.loads(c.capture(w)).state()==w.state()
    object.__setattr__(w.events[0],'kind','developer edit')
    c.invalidate();assert pickle.loads(c.capture(w)).state()==w.state()


def test_immutable_bundle_does_not_observe_future_ticks():
    w=TerrainWorld();w.step(500);c=Chronicle();warm(c,w);expected=pickle.loads(pickle.dumps(w.state()));bundle=c.detach(w)
    assert isinstance(bundle.hot,bytes) and all(isinstance(b,bytes) for b in bundle.events)
    assert all(isinstance(b,bytes) for i,b in bundle.dead)
    w.events[0].detail['changed after capture']=True
    w.slots[:]=[None]*60;w.request('rain',5,5);w.step(30);c.prepare(w,.01)
    assert bundle.restore().state()==expected
    rebuilt=c.detach(w).restore();assert rebuilt.state()==w.state()
    w.step(20);rebuilt.step(20);assert rebuilt.state()==w.state()


def test_corrupted_preparation_worker_retry_retains_prior_commit(tmp_path):
    import pytest
    from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
    from gnome_fortress.terrain_storage import save_game,load_game
    w=TerrainWorld();w.step(500);path=tmp_path/'cache-error.g5.sqlite';save_game(w,path);raw=path.read_bytes()
    worker=TerrainCheckpointWorker()
    try:
        warm(worker.chronicle,w);worker.chronicle.blocks[0].payload=b'corrupt';w.step()
        worker.start(w,path)
        with pytest.raises(pickle.UnpicklingError):worker.future.result(timeout=10)
        with pytest.raises(pickle.UnpicklingError):worker.poll()
        assert not worker.chronicle.blocks and path.read_bytes()==raw
        worker.start(w,path);worker.future.result(timeout=10);worker.poll()
        assert load_game(path).state()==w.state()
    finally:worker.close()


def test_instrumentation_preserves_dataclass_value_equality():
    from gnome_fortress.model import Event,Episode
    w=TerrainWorld();w.step(500);c=Chronicle();warm(c,w)
    event=w.events[0];copy=Event(**asdict(event))
    assert event==copy and copy==event and copy in w.events
    dead=next(a for a in w.agents.values() if not a.alive)
    episode=dead.memories[0];assert episode==Episode(**asdict(episode))
    w.events.remove(copy)
    assert pickle.loads(c.capture(w)).state()==w.state()


def test_two_preparers_handoff_invalidates_previous_cached_notifications():
    w=TerrainWorld();w.step(500);first=Chronicle();second=Chronicle()
    warm(first,w);old=first.detach(w);expected=pickle.loads(pickle.dumps(w.state()))
    warm(second,w);assert not first.blocks
    w.events[0].detail['new value']=3
    dead=next(a for a in w.agents.values() if not a.alive);dead.health=-8
    assert first.detach(w).restore().state()==w.state()
    assert second.detach(w).restore().state()==w.state()
    assert old.restore().state()==expected
