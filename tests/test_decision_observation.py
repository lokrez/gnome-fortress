"""G8B execution evidence; synthetic branches are explicitly controlled fixtures."""
import copy
import inspect
import os
import pickle
import subprocess
import sys
import types

import pytest
from gnome_fortress.engine import World
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.decision_observation import DecisionObservation, for_world
from gnome_fortress.terrain_checkpoint import capture_snapshot
from gnome_fortress.chronicle import Chronicle
from gnome_fortress.terrain_storage import save_game, load_game


def accepted_world():
    source = subprocess.check_output(['git','show',
        'bf6e5568056e75f07cd7b9d468a592fc5e5abf6f:gnome_fortress/engine.py'],text=True)
    module = types.ModuleType('gnome_fortress._g8b_accepted_engine')
    module.__package__ = 'gnome_fortress'
    exec(compile(source,'<accepted G8A.2 engine>','exec'),module.__dict__)
    return module.World


def inputs(w):
    if w.tick==0:
        w.request('rain',5,5,duration=20);w.request('rupture',5,5)
    if w.tick==9:w.request('drought',5,5,duration=30)
    if w.tick==20:w.request('rewild',5,5)
    if w.tick==29:
        x,y=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain=='rock')
        w.request('wellspring',x,y)


@pytest.mark.parametrize('seed',[1,42])
def test_accepted_disabled_enabled_exact(seed,monkeypatch):
    reference = accepted_world()
    # TerrainWorld's inherited biology/decisions are unchanged; use the accepted
    # engine's step and methods for A, including original scheduling/RNG calls.
    import gnome_fortress.terrain_game as terrain_module
    a,b,c = (TerrainWorld(seed) for _ in range(3))
    o=DecisionObservation();assert o.start(c,1)
    for boundary in (1,10,21,40,100,500):
        while b.tick<boundary:
            for w in (a,b,c):inputs(w)
            with monkeypatch.context() as m:
                m.setattr(terrain_module,'World',reference)
                # Bind accepted methods as well, not only its tick loop.
                for name in ('decide','move','remember','_biology','schedule'):
                    m.setattr(type(a),name,getattr(reference,name))
                a.step()
            b.step();c.step()
        assert a.state()==b.state()==c.state()
        assert a.rng.getstate()==c.rng.getstate()
    assert o.records and o.error is None
    # Exact scoring and action bytecode/source remains the accepted implementation.
    for method in ('decide','move','remember','_biology','schedule'):
        assert getattr(World,method).__code__.co_code == getattr(reference,method).__code__.co_code


def isolated():
    w=TerrainWorld(1)
    # Only agent 1 acts; all other founders stay alive asleep in these fixtures.
    for a in w.agents.values():a.sleep_until=100
    a=w.agents[1];a.sleep_until=0;a.x=a.y=3
    a.cooldown=100;a.hunger=a.thirst=a.fatigue=0
    for row in w.cells:
        for c in row:c.terrain='grass';c.food=0
    o=DecisionObservation();o.start(w,1)
    return w,a,o


@pytest.mark.parametrize('action',['drink','eat','sleep','wait','move'])
def test_real_action_branches(action):
    w,a,o=isolated()
    if action=='drink':a.thirst=30;w.cell(3,2).terrain='water'
    if action=='eat':a.hunger=30;w.cell(3,3).food=20
    if action=='sleep':a.fatigue=65
    if action=='wait':
        for x,y in w.neighbors(a.x,a.y):w.cell(x,y).terrain='rock'
    w.step();r=o.records[-1];d=r['decision']
    assert r['scheduled'] and d['action']==action and d['complete']
    assert d['before']['thirst']==r['biology_after']['thirst']
    if action=='move':
        m=d['movement'];assert m['destination']==[a.x,a.y]
        selected=next(c for c in m['candidates'] if [c['x'],c['y']]==m['destination'])
        assert selected['score']==m['best']
        assert m['tied'] and m['choice_called']
    if action in ('drink','eat','move'):
        for change in d['learning']:
            assert change['current']==a.learned[change['key']]
            assert change['current']==max(-100,min(100,(3*change['previous']+change['reward'])//4))


def test_hazard_learning_and_death_are_not_an_invented_action():
    w,a,o=isolated();a.health=1
    for x,y in w.neighbors(a.x,a.y):w.cell(x,y).terrain='hazard'
    w.step();r=o.records[-1];d=r['decision']
    assert d['action']=='move' and d['after']['action']=='dead'
    assert d['after']['death_cause']=='hazard'
    assert d['learning'][0]['reward']<0 and d['learning'][0]['current']<0
    assert [e['kind'] for e in d['events']]==['hazard','death']
    assert not o.enabled and for_world(w) is None
    old=copy.deepcopy(list(o.records));w.step(3);assert list(o.records)==old


def test_biology_death_sleep_and_eligible_no_slot():
    w,a,o=isolated();a.health=1;a.thirst=110
    w.step();r=o.records[-1]
    assert not r['scheduled'] and r['decision'] is None
    assert 'biology' in r['status'] and r['biology_after']['death_cause']=='dehydration'
    w,a,o=isolated();a.sleep_until=10;w.step()
    assert o.records[-1]['decision'] is None and 'sleeping' in o.records[-1]['status']
    w,a,o=isolated()
    for other in w.agents.values():other.sleep_until=0
    child=w._spawn(3,3,a.traits,(1,2));o.start(w,child.id)
    w.step();assert not o.records[-1]['scheduled']
    assert 'not assigned' in o.records[-1]['status']


def test_natural_social_reproduction_and_partner_changes():
    found=set()
    for identity in range(1,21):
        w=TerrainWorld(1);o=DecisionObservation();o.start(w,identity)
        for _ in range(400):
            w.step()
            d=o.records[-1]['decision'] if o.records else None
            if d and d['action'] in ('socialize','reproduce'):
                found.add(d['action'])
                assert d['random_attempt_count']>0 and d['events']
                if d['action']=='reproduce':
                    assert any(p['after']['children']>p['before']['children'] for p in d['peers'])
            if len(found)==2:break
        if len(found)==2:break
    assert found=={'socialize','reproduce'}


def test_value_only_bounds_switch_stop_and_no_checkpoint_fields(tmp_path):
    w=TerrainWorld();o=DecisionObservation(4);o.start(w,1);w.step(10)
    assert len(o.records)==4
    original=copy.deepcopy(list(o.records));w.agents[1].health=42
    assert list(o.records)==original
    assert not any('observ' in k for k in vars(w))
    restored=pickle.loads(capture_snapshot(w));assert restored.state()==w.state()
    assert for_world(restored) is None
    p=tmp_path/'observed.g5.sqlite';save_game(w,p);loaded=load_game(p)
    assert loaded.state()==w.state() and for_world(loaded) is None
    o.stop(w);assert list(o.records)==original
    o.start(w,2);assert not o.records
    assert not o.start(w,999999)


def test_chronicle_preparation_and_detached_continuation(tmp_path):
    w=TerrainWorld(2);o=DecisionObservation();o.start(w,1);cache=Chronicle()
    w.step(40)
    for _ in range(30):cache.prepare(w)
    expected=w.state();snapshot=cache.detach(w);w.step(50)
    restored=snapshot.restore();assert restored.state()==expected
    restored.step(50);assert restored.state()==w.state()
    assert for_world(restored) is None


def test_other_tracer_and_observation_failure_do_not_change_decision(monkeypatch):
    w=TerrainWorld();r=TerrainWorld();o=DecisionObservation();o.start(w,1)
    def debugger(frame,event,arg):return debugger
    sys.settrace(debugger)
    try:w.step()
    finally:sys.settrace(None)
    r.step();assert r.state()==w.state()
    assert 'another Python tracer' in o.error
    assert o.records[-1]['decision']['action'] is None
    # A failed value snapshot happens before invocation; the decision still runs once.
    import gnome_fortress.decision_observation as module
    def broken(a):raise ValueError('controlled observation error')
    monkeypatch.setattr(module,'values',broken)
    w.step();r.step();assert r.state()==w.state()


def test_ui_controls_scroll_death_and_cadence(tmp_path):
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from gnome_fortress.living_viewer import LivingObserver
    from gnome_fortress.decision_presentation import observation_lines
    w=TerrainWorld(1);reference=TerrainWorld(1)
    v=LivingObserver(w,paused=True,window_size=(1280,720))
    try:
        before=w.state();v.navigate('decisions');v.draw()
        assert 'No decision recorded.' in observation_lines(v.current_decision_record())
        v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_u)])
        v.draw();assert v.decisions.enabled and w.state()==before
        for _ in range(20):
            v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_PERIOD)])
            v.advance(0);reference.step();v.draw();v.draw()
        assert w.state()==reference.state()
        v.action('decision-older');tick=v.current_decision_record()['tick']
        w.step();v.draw();assert v.current_decision_record()['tick']==tick
        before=w.state();v.action('decision-details');v.scroll_panel(100);v.draw()
        v.action('center');v.action('follow');v.action('tab:life');v.draw()
        assert w.state()==before
        v.action('decision-observe');assert not v.decisions.enabled
        v.select_individual(2);assert not v.decisions.records
        v.action('decision-observe');w.agents[2].health=1;w.agents[2].thirst=140
        w.step();v.draw();assert v.selected==2 and not v.decisions.enabled
        assert 'biology' in v.current_decision_record()['status']
        for size in ((800,600),(1280,720),(3840,2160)):
            v.screen=pygame.display.set_mode(size);v.layout(size);v.draw()
            assert v.tabs['decisions'][0].colliderect(v.panel_rect)
            assert v.body.bottom<=size[1]
    finally:pygame.quit()


def test_tracer_install_failure_is_read_only(monkeypatch):
    w,r=TerrainWorld(),TerrainWorld();o=DecisionObservation();o.start(w,1)
    def refused(trace):raise RuntimeError('controlled tracing refusal')
    monkeypatch.setattr(sys,'settrace',refused)
    w.step();r.step();assert w.state()==r.state()
    assert not o.records[-1]['decision']['complete']


def test_negative_floor_learning_contribution_and_unique_best():
    w,a,o=isolated();a.learned['move:hazard']=-1
    for x,y in w.neighbors(a.x,a.y):w.cell(x,y).terrain='hazard'
    w.cell(4,3).terrain='forest'
    w.step();d=o.records[-1]['decision'];m=d['movement']
    assert all(c['learned_contribution']==-1 for c in m['candidates'] if c['terrain']=='hazard')
    assert m['destination']==[4,3] and not m['tied']
    assert d['learning'][0]['key']=='move:forest'


def test_biology_events_and_exact_observed_checkpoint_bytes():
    w,r=TerrainWorld(),TerrainWorld();o=DecisionObservation();o.start(w,1)
    w.step(100);r.step(100)
    assert capture_snapshot(w)==capture_snapshot(r)
    w,a,o=isolated();a.health=1;a.thirst=140;w.step()
    row=o.records[-1];e=row['biology_events'][0]
    assert e['kind']=='death' and w.events[e['index']].actor==a.id
    assert e['detail']['cause']==a.death_cause


def test_engine_exception_not_swallowed_or_retried():
    w,a,o=isolated();o.begin(w);o.after_biology(w);calls=[]
    def failing(agent):
        calls.append(agent.id)
        raise RuntimeError('controlled engine failure')
    with pytest.raises(RuntimeError,match='engine failure'):o.invoke(w,a,failing)
    assert calls==[1] and not o.pending['decision']['complete']


def test_natural_observed_life_through_biological_death_matches_reference():
    reference=accepted_world()(1);w=World(1);o=DecisionObservation();o.start(w,1)
    w.step(2050);reference.step(2050)
    assert w.state()==reference.state()
    assert w.rng.getstate()==reference.rng.getstate()
    assert w.agents[1].died==2048 and o.records[-1]['decision'] is None
    assert o.records[-1]['biology_events'][0]['detail']['cause']=='old_age'


def test_observed_snapshots_at_queued_active_and_terrain_boundaries():
    a,b=TerrainWorld(42),TerrainWorld(42);o=DecisionObservation();o.start(b,1)
    c=Chronicle()
    for boundary in (0,1,9,10,20,21,29,30,31,50,80):
        while a.tick<boundary:
            inputs(a);inputs(b);a.step();b.step();c.prepare(b)
        assert a.state()==b.state()
        snapshot=c.detach(b);restored=snapshot.restore()
        assert restored.state()==a.state() and for_world(restored) is None
        # The captured payload stays at T even after the live world advances.
        first=pickle.loads(capture_snapshot(a));first.step(3);restored.step(3)
        assert first.state()==restored.state()


def test_ui_oldest_entry_eviction_keeps_browsing_coherent():
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from gnome_fortress.living_viewer import LivingObserver
    w=TerrainWorld();v=LivingObserver(w,paused=True,window_size=(1280,720))
    try:
        v.action('decision-observe');w.step(10)
        v.decision_tick=1;w.step(150)
        oldest=v.current_decision_record()['tick']
        assert oldest==v.decisions.records[0]['tick']==v.decision_tick
        v.action('decision-newer');assert v.current_decision_record()['tick']==oldest+1
    finally:pygame.quit()


def test_missing_execution_source_reports_unavailable_without_world_changes(monkeypatch):
    w=TerrainWorld();o=DecisionObservation();before=w.state()
    def absent(function):raise OSError('controlled missing source')
    monkeypatch.setattr(inspect,'getsourcelines',absent)
    assert not o.start(w,1) and not o.enabled and for_world(w) is None
    assert 'source unavailable' in o.error and w.state()==before


def test_dense_peer_evidence_and_attempts_are_bounded():
    w,a,o=isolated()
    while len(w.agents)<200:w._spawn(3,3,a.traits,(1,2))
    for agent in w.agents.values():
        agent.x=agent.y=3;agent.sleep_until=0;agent.age=200
        agent.cooldown=0;agent.hunger=agent.thirst=0
        agent.traits['fertility']=agent.traits['sociability']=0
    w.step();d=o.records[-1]['decision']
    assert d['nearby_count']==199 and len(d['peers'])==64
    assert d['random_attempt_count']>64 and len(d['random_attempts'])==64
    assert len(d['movement']['observed_peers'])==64
    assert d['complete'] and o.error is None


def test_observed_extinction_never_creates_a_final_decision():
    w,a,o=isolated()
    for other in list(w.living()):
        if other.id!=a.id:w.kill(other,'test')
    a.health=1;a.thirst=140;w.step()
    assert w.extinct and not o.enabled and o.records[-1]['decision'] is None
    before=w.state();records=copy.deepcopy(list(o.records));w.step(5)
    assert w.state()==before and list(o.records)==records
