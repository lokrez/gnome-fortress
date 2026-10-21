"""G8C adversarial history capture; no biological/terrain rules changed."""
import copy,json,pickle
from dataclasses import asdict
import pytest
from gnome_fortress.chronicle import Chronicle,EventJournal
from gnome_fortress.chronicle_index import AgentJournal
from gnome_fortress.terrain_checkpoint import capture_snapshot
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.model import Agent,Episode


def warm(c,w):
    for _ in range(20000):
        c.prepare(w,.01)
        if len(w.events)-c.prepared<128 and not c.dead_queue and not c.dirty:return
    raise AssertionError('cache did not converge')


def equal(c,w):
    expected=pickle.loads(capture_snapshot(w)).state()
    assert c.detach(w).restore().state()==expected==w.state()


@pytest.fixture
def prepared():
    w=TerrainWorld(1);w.step(500);c=Chronicle();warm(c,w);return w,c


@pytest.mark.parametrize('mutation',[
    lambda w:setattr(w.events[0],'kind','edited'),
    lambda w:w.events[0].detail['parents'].append(123),
    lambda w:w.events[0].detail.update(nested={'a':[{'x':1}]}),
    lambda w:w.events.__setitem__(0,w.events[1]),
    lambda w:w.events.__setitem__(slice(1,3),[w.events[4]]),
    lambda w:w.events.append(copy.deepcopy(w.events[-1])),
    lambda w:w.events.reverse(),
    lambda w:setattr(w,'events',list(w.events)),
    lambda w:setattr(w,'agents',dict(w.agents)),
])
def test_supported_history_mutations(prepared,mutation):
    w,c=prepared;old=c.detach(w);before=w.state();mutation(w)
    equal(c,w);assert old.restore().state()==before


def test_nested_event_and_terminal_agent_edits(prepared):
    w,c=prepared;e=w.events[0]
    e.detail['nested']={'items':[{'leaf':[1]}]};equal(c,w);warm(c,w)
    e.detail['nested']['items'][0]['leaf'] += [2];equal(c,w)
    dead=next(a for a in w.agents.values() if not a.alive)
    dead.relationships[999]=42;dead.memories[0].reward-=1
    dead.memories.append(Episode(w.tick,'move',dead.x,dead.y,'grass',0));equal(c,w)
    dead.memories[-1].feature={'nested':[1]};warm(c,w)
    dead.memories[-1].feature['nested'].append(2);equal(c,w)


def test_replacement_deletion_and_rewind(prepared):
    w,c=prepared;dead=next(a for a in w.agents.values() if not a.alive)
    data=asdict(dead);data['memories']=[Episode(**m) for m in data['memories']]
    w.agents[dead.id]=Agent(**data);w.agents[dead.id].relationships[777]=11;equal(c,w);warm(c,w)
    del w.agents[dead.id];equal(c,w) # Invalid as a saved model, but capture must not retain ghosts.
    w.tick-=1;equal(c,w)
    other=TerrainWorld(42);equal(c,other)


@pytest.mark.parametrize('prepared',[False,True])
def test_snapshot_does_not_see_future(prepared):
    w=TerrainWorld(1);w.step(500);c=Chronicle()
    for kind in ('rain','drought','rupture','rewild','wellspring'):w.request(kind,5,5)
    if prepared:w.step(3);warm(c,w)
    expected=w.state();snapshot=c.detach(w)
    w.step(90);w.request('rewild',5,5);w.step(2)
    w.events[0].detail['future']=[1,2]
    dead=next(a for a in w.agents.values() if not a.alive);dead.memories[0].reward-=1
    c.prepare(w,.01)
    assert snapshot.restore().state()==expected


def test_internal_corruption_and_low_level_contract(prepared):
    w,c=prepared;good=c.detach(w);before=w.state()
    c.blocks[0].payload=b'not a valid pickle'
    with pytest.raises(pickle.UnpicklingError):c.detach(w).restore()
    assert good.restore().state()==before
    c.invalidate();warm(c,w)
    object.__setattr__(w.events[0],'kind','explicit bypass')
    c.invalidate();equal(c,w)
    c.invalidate();warm(c,w)
    # Direct edits through adopted-container aliases bypass journals by contract.
    w.events.data[0]=w.events[1];c.invalidate();equal(c,w)


def test_normal_container_semantics_and_bounded_queue(prepared):
    w,c=prepared;events=EventJournal([1,2]);events+=events
    assert list(events)==[1,2,1,2] and events==[1,2,1,2]
    mapping=AgentJournal({1:'a',2:'b'});assert mapping.popitem()==(2,'b')
    dead=next(a for a in w.agents.values() if not a.alive)
    for _ in range(100):w.agents[dead.id]=dead;c.bind(w)
    assert list(c.dead_queue).count(dead.id)==1
    equal(c,w)


def test_no_clean_historical_record_scan(prepared,monkeypatch):
    w,c=prepared
    def forbidden(*args):raise AssertionError('Warm capture scanned historical blocks')
    for block in c.blocks:monkeypatch.setattr(block,'encode',forbidden)
    for block in c.dead.values():monkeypatch.setattr(block,'encode',forbidden)
    equal(c,w)
    assert len(c.hot_ids)==len(w._living_agents)


def test_controlled_extinction_and_queued_intervention():
    w=TerrainWorld();w.step(50);w.request('rain',3,3)
    for a in list(w.living()):w.kill(a,'hazard')
    assert w.extinct;c=Chronicle();warm(c,w);equal(c,w)
    clone=c.detach(w).restore();clone.step(10);w.step(10);assert clone.state()==w.state()


def test_owner_loop_defers_manual_save_without_losing_request(tmp_path):
    import os
    os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
    from concurrent.futures import Future
    from gnome_fortress.god_viewer import run
    from gnome_fortress.living_viewer import LivingObserver
    from gnome_fortress.terrain_storage import save_game,load_game
    w=TerrainWorld();p=tmp_path/'deferred.g5.sqlite';instances=[];views=[]
    class ControlledGate:
        locks_world=False
        def __init__(self,callback):self.callback=callback;self.future=None;self.calls=0;self.started=[];instances.append(self)
        @property
        def pending(self):return self.future is not None
        def prepare(self,world):self.calls+=1
        def prepared_for(self,world):return self.calls>=4
        def start(self,world,path):
            assert self.calls>=4;self.started.append(world.tick)
            self.future=Future();self.future.set_result(self.callback(world,path))
        def poll(self):f,self.future=self.future,None;return f.result()
        def close(self):assert self.future is None
    class View(LivingObserver):
        def __init__(self,*args):
            super().__init__(*args,window_size=(1280,720));self.save_requested=True;self.notices=[];views.append(self)
        def handle(self,events):
            super().handle(events);self.notices.append(self.notice)
            worker=instances[0]
            if worker.calls<4:assert self.save_requested and not worker.pending
            if worker.started and not worker.pending:self.running=False
    run(w,p,save_game,checkpoint_ticks=100000,max_frames=12,observer_class=View,worker_class=ControlledGate)
    assert len(instances[0].started)==1
    assert any('Preparing history for save' in n for n in views[0].notices)
    assert any('Saved tick' in n for n in views[0].notices)
    assert load_game(p).tick==instances[0].started[0]
