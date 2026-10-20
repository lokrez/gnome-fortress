import copy
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'

import pygame

from gnome_fortress.game import GameWorld
from gnome_fortress.life_presentation import LifeHistory,event_role,life_event_text,life_summary
from gnome_fortress.god_viewer import GodObserver
from gnome_fortress.model import Event


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)


def test_attribution_all_recorded_roles_and_no_proximity_inference():
    pairs=[(Event(1,'birth',3,None,dict(parents=[1,2])),{1:'parent',2:'parent',3:'born'}),
           (Event(1,'reproduce',1,2,dict(child=3)),{1:'parent (actor)',2:'parent (partner)',3:'child'}),
           (Event(2,'social',1,2,dict(reward=5)),{1:'initiator',2:'recipient'}),
           (Event(3,'hazard',2,None,dict(damage=17)),{2:'injured'}),
           (Event(4,'death',1,None,dict(cause='hazard')),{1:'deceased'})]
    for event,roles in pairs:
        for identity in range(1,5):assert event_role(event,identity)==roles.get(identity)
    assert '17 health lost' in life_event_text(pairs[3][0],2)
    assert event_role(Event(2,'divine_request',None,None,dict(x=1,y=1)),1) is None
    assert event_role(Event(1,'birth',5,None,dict(parents=None)),1) is None


def test_objective_history_survives_memory_eviction_and_empty_history():
    w=GameWorld();a=w.agents[1];w.event('hazard',1,damage=12)
    for _ in range(70):w.remember(a,'move','grass',0)
    assert len(a.memories)==64
    history=LifeHistory(w);history.select(1)
    assert [e.kind for _,e in history.page()]==['birth','hazard']
    assert life_summary(w,1)['born']==0 and life_summary(w,1)['age']>=120
    w.events=[];history.update()
    assert not history.positions and not history.page()
    assert life_summary(w,9999) is None


def test_family_lookup_incremental_bounded_and_missing_sources():
    w=GameWorld();h=LifeHistory(w);h.select(1)
    for _ in range(45):w._spawn(1,1,w.agents[1].traits,(1,2))
    h.update();initial=h.agents_examined
    page=h.family(12,4)
    assert len(h.children)==45 and [r['id'] for r in page['children']]==[73,74,75,76]
    for _ in range(20):h.update();assert len(h.family(40,3)['children'])==3
    assert h.agents_examined==initial
    h.select(61);assert [p['id'] for p in h.family()['parents']]==[1,2]
    del w.agents[2]
    assert h.family()['parents'][1]['status']=='record unavailable'
    assert h.family()['parents'][1]['born'] is None


class CountedEvents(list):
    def __init__(self,values):super().__init__(values);self.reads=0
    def __iter__(self):raise AssertionError('Full historical iteration')
    def __getitem__(self,key):
        if isinstance(key,slice):
            assert len(range(*key.indices(len(self))))<=5
            self.reads+=len(range(*key.indices(len(self))))
        else:self.reads+=1
        return super().__getitem__(key)


def test_long_history_one_selected_cache_no_rescan_each_frame():
    w=GameWorld();w.events=CountedEvents([Event(i,'social',1,2,dict(reward=3)) for i in range(20000)])
    v=GodObserver(w,paused=True)
    try:
        v.handle([key(pygame.K_F3)]);v.draw()
        assert len(v.life.positions)==20000
        reads=w.events.reads;examined=v.life.records_examined;agent_reads=v.life.agents_examined
        for _ in range(8):v.draw()
        assert v.life.records_examined==examined and v.life.agents_examined==agent_reads
        assert w.events.reads-reads<=8*(3+v.event_capacity+v.life_capacity)
        w.events.append(Event(20001,'hazard',1,None,dict(damage=12)));v.draw()
        assert v.life.records_examined==examined+1
        old=v.life.positions;v.select_individual(3);v.draw()
        assert v.life.positions is not old and not v.life.positions
    finally:pygame.quit()


def test_watch_identity_stable_birth_sleep_death_overlap_and_selection():
    w=GameWorld();v=GodObserver(w,paused=True)
    try:
        # Controlled overlap/death fixture; no claim that these events arose naturally.
        for a in w.agents.values():a.x=a.y=1
        v.handle([key(pygame.K_F3),key(pygame.K_w)]);v.draw()
        assert v.watch_id==v.selected==1
        a=w.agents[1];a.sleep_until=12
        w._spawn(1,1,a.traits,(1,2));v.draw()
        assert v.watch_id==v.selected==1
        w.kill(a,'hazard');v.draw()
        assert v.watch_id==v.selected==1
        snapshot=life_summary(w,1)
        assert snapshot['location_kind']=='final stored' and snapshot['died']==0
        v.select_individual(2);assert v.watch_id is None and v.selected==2
        v.handle([key(pygame.K_w),key(pygame.K_w)]);assert v.watch_id is None
    finally:pygame.quit()


def test_many_deceased_family_click_and_stable_chronological_scroll():
    w=GameWorld();a=w.agents[1];child=w._spawn(1,1,a.traits,(1,2))
    for identity in range(3,60):w.kill(w.agents[identity],'fixture')
    for tick in range(40):w.events.append(Event(tick,'social',1,2,dict(reward=2)))
    v=GodObserver(w,paused=True)
    try:
        v.handle([key(pygame.K_F3),key(pygame.K_w)]);v.draw();v.browse_life(-8);v.draw()
        start=v.life_start;page=[i for i,_ in v.life.page(start,v.life_capacity)]
        w.event('hazard',1,damage=13);v.draw()
        assert v.life_start==start and [i for i,_ in v.life.page(start,v.life_capacity)]==page
        assert [e.tick for _,e in v.life.page(start,v.life_capacity)]==sorted(e.tick for _,e in v.life.page(start,v.life_capacity))
        v.life_pane='family';v.draw()
        row=next(r for r,identity in v.family_hits if identity==child.id)
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=row.center)])
        assert v.selected==child.id and v.watch_id is None
        v.draw();assert v.life.family()['parents'][0]['id']==1
    finally:pygame.quit()


def test_watch_inspection_render_cadence_does_not_change_simulation():
    a,b=GameWorld(9),GameWorld(9);v=GodObserver(a,paused=True)
    try:
        for w in (a,b):w.request('rain',2,2,5,25);w.request('drought',3,2,2,11)
        v.handle([key(pygame.K_F3),key(pygame.K_w)])
        before=copy.deepcopy(a.state());rng=a.rng.getstate()
        v.draw();v.life_pane='family';v.draw();v.life_pane='events';v.browse_life(-3);v.draw()
        assert a.state()==before and a.rng.getstate()==rng
        for tick in range(35):
            v.handle([key(pygame.K_PERIOD)]);v.advance(0)
            for _ in range(tick%3):v.draw()
        b.step(35);assert a.state()==b.state()
    finally:pygame.quit()


def test_many_dead_children_family_pages_do_not_recurse_or_replace_watch():
    w=GameWorld()
    for _ in range(500):
        child=w._spawn(1,1,w.agents[1].traits,(1,2));w.kill(child,'controlled_fixture')
    v=GodObserver(w,paused=True)
    try:
        v.handle([key(pygame.K_F3),key(pygame.K_w)]);v.life_pane='family';v.draw()
        v.browse_life(400);v.draw()
        assert len(v.life.children)==500 and len(v.family_hits)<=2+v.family_capacity
        assert all(member['status']=='deceased' for member in v.life.family(400,3)['children'])
        assert v.watch_id==v.selected==1
        v.select_individual(500);v.draw()
        assert v.selected==500 and life_summary(w,500)['location_kind']=='final stored'
    finally:pygame.quit()


def test_failed_periodic_save_does_not_spin_and_manual_save_can_recover(tmp_path,monkeypatch):
    import time
    from gnome_fortress import god_viewer
    calls=[];seen=[]
    class Inspector(GodObserver):
        def __init__(self,*args,**kw):super().__init__(*args,**kw);self.frame=0;seen.append(self)
        def handle(self,events):
            super().handle(events);self.frame+=1
            if self.frame==1:self.world.step()  # Controlled overdue periodic save.
            if self.frame==6:self.save_requested=True  # Explicit S-style retry.
    class Clock:
        def tick(self,hz):time.sleep(.01);return 0
    def writer(world,path):
        calls.append(world.tick)
        if len(calls)==1:raise OSError('controlled disk failure')
        return {'tick':world.tick}
    monkeypatch.setattr(god_viewer,'GodObserver',Inspector)
    monkeypatch.setattr(pygame.time,'Clock',Clock)
    god_viewer.run(GameWorld(),tmp_path/'retry.g1.sqlite',writer,checkpoint_ticks=1,paused=True,max_frames=10)
    assert calls==[1,1] and seen[0].paused
    assert 'Saved tick 1'==seen[0].notice
