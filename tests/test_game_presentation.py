import copy
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'

import pygame

from gnome_fortress.game import GameWorld
from gnome_fortress.game_presentation import EventIndex, WorldPresentation, agent_view, event_text
from gnome_fortress.god_viewer import GodObserver
from gnome_fortress.model import Event


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)


def test_real_event_filter_format_and_incremental_index():
    w=GameWorld();index=EventIndex(w.events)
    assert len(index.positions)==60 and index.seen==60
    w.event('social',1,2,reward=3)
    w.event('hazard',1,damage=17,x=1,y=1)
    w.request('rain',1,1)
    assert index.update(w.events)==2
    page=index.page(count=2)
    assert [e.kind for _,e in page]==['divine_request','hazard']
    assert 'rain requested' in event_text(page[0][1],w)
    assert '00001' in event_text(page[1][1],w) and '17 health lost' in event_text(page[1][1],w)
    scanned=index.records_examined
    for _ in range(30):assert index.update(w.events)==0
    assert index.records_examined==scanned
    assert all(e.kind!='social' for _,e in index.page(count=100))


class CountedEvents(list):
    def __init__(self,values):super().__init__(values);self.reads=0
    def __iter__(self):raise AssertionError('Full iteration of event history')
    def __getitem__(self,key):
        if isinstance(key,slice):
            assert len(range(*key.indices(len(self))))<=5,'Historical full slice'
            self.reads+=len(range(*key.indices(len(self))))
        else:self.reads+=1
        return super().__getitem__(key)


def test_long_event_history_no_full_rescan_during_update_or_draw():
    w=GameWorld()
    events=CountedEvents([Event(i,'hazard',1,None,dict(damage=12)) for i in range(20000)])
    w.events=events
    viewer=GodObserver(w,paused=True)
    try:
        initial=events.reads
        for _ in range(10):viewer.draw()
        # The base observer reads three recent records; the feed reads its bounded page.
        assert events.reads-initial<=10*(3+viewer.event_capacity)
        assert viewer.presentation.events.records_examined==20000
        events.append(Event(20000,'death',1,None,dict(cause='hazard')))
        viewer.draw()
        assert viewer.presentation.events.records_examined==20001
    finally:pygame.quit()


def test_resource_totals_live_overlap_and_remaining_ticks():
    w=GameWorld();w.step(9)
    a=w.request('rain',1,1,2,20);d=w.request('drought',1,1,0,1);b=w.request('rain',1,1,2,20)
    p=WorldPresentation(w)
    assert p.status['active']==0
    assert p.powers[1]['future_active_ticks']==1
    w.step();p.refresh()
    assert p.status['active']==3
    assert p.powers[0]['overlap']=='partially overridden'
    assert p.powers[2]['overlap']=='overridden'
    assert p.powers[1]['status']=='active' and p.powers[1]['future_active_ticks']==0
    assert p.powers[1]['activation']==10 and p.powers[1]['expires']==11
    assert p.powers[0]['totals']==a.totals and p.powers[1]['totals']==d.totals
    assert p.status['food_stock']==sum(c.food for row in w.cells for c in row)
    assert p.status['born']==len(w.agents) and p.status['deaths']==len(w.agents)-len(w.living())
    assert p.status['net_population_change']==len(w.living())-60
    before=copy.deepcopy(w.state());p.refresh();assert w.state()==before
    w.step();p.refresh()
    assert p.powers[1]['status']=='expired' and p.powers[1]['future_active_ticks']==0
    assert p.powers[0]['overlap']==''  # Current overlap changes BEFORE another food pulse.
    assert p.powers[2]['overlap']=='overridden'
    assert b.status=='active'  # Derived overlap does not change canonical lifecycle.


def test_inspection_uses_actual_fields_and_preserves_state_rng():
    w=GameWorld();w.step(3);a=w.agents[1]
    child=w._spawn(a.x,a.y,a.traits,(1,2));a.sleep_until=w.tick+12
    w.kill(w.agents[3],'hazard')
    before=copy.deepcopy(w.state());rng=w.rng.getstate()
    assert agent_view(w,1)['status']=='sleeping'
    assert agent_view(w,3)['status']=='deceased'
    assert agent_view(w,3)['death_cause']=='hazard'
    assert agent_view(w,child.id)['parents']==(1,2)
    assert agent_view(w,child.id)['status']=='awake'
    assert len(agent_view(w,1)['memories'])<=3
    assert agent_view(w,999999) is None
    assert w.state()==before and w.rng.getstate()==rng


def test_browsing_tabs_inspection_and_feed_anchor_are_read_only():
    w=GameWorld();v=GodObserver(w,paused=True)
    try:
        before=w.state();rng=w.rng.getstate()
        v.draw();v.handle([key(pygame.K_PAGEUP),key(pygame.K_F2)])
        offset=v.event_offset
        assert offset>0 and v.tab=='powers'
        # New meaningful events preserve the currently browsed page.
        w.event('hazard',1,damage=12)
        v.sync();assert v.event_offset==offset+1
        v.handle([key(pygame.K_END),key(pygame.K_F1),key(pygame.K_TAB)])
        assert v.event_offset==0 and v.tab=='gnome'
        v.draw()
        assert w.rng.getstate()==rng
        after=w.state();after['events'].pop()
        assert after==before
    finally:pygame.quit()


def test_live_notice_and_render_frequencies_same_world():
    a,b=GameWorld(4),GameWorld(4);v=GodObserver(a,paused=True)
    try:
        v.handle([key(pygame.K_r),pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(1,1))])
        b.request('rain',0,0)
        assert 'queued' in v.notice_text() and v.tab=='powers'
        for tick in range(30):
            v.handle([key(pygame.K_PERIOD)]);v.advance(0)
            for _ in range(tick%4):v.draw()
        b.step(30)
        assert 'active' in v.notice_text() and a.state()==b.state()
        a.step(171);v.draw()
        assert 'expired' in v.notice_text()
    finally:pygame.quit()


def test_missing_optional_inspection_values_and_event_source():
    w=GameWorld();a=w.agents[1];a.memories=[];a.learned={}
    view=agent_view(w,1)
    assert view['memories']==() and view['movement']=={}
    assert 'unavailable' in event_text(Event(0,'death',None,None,{}),w)
    v=GodObserver(w,paused=True)
    try:v.draw()
    finally:pygame.quit()


def test_nonstacking_visual_coverage_and_drought_dominance():
    w=GameWorld();w.request('rain',2,2,2,20);w.step()
    p=WorldPresentation(w);single=dict(p.region_cells)
    w.request('rain',2,2,2,20);w.step();p.refresh()
    assert p.region_cells==single
    w.request('drought',2,2,0,1);w.step();p.refresh()
    assert p.region_cells[2,2]=='drought'
    assert all(v=='rain' for xy,v in p.region_cells.items() if xy!=(2,2))
    w.step();p.refresh();assert p.region_cells==single


def test_g1_fixture_loads_without_modifying_file_or_state(tmp_path):
    import gzip,json
    from pathlib import Path
    from gnome_fortress.game_storage import load_game,save_game
    fixture=Path(__file__).resolve().parents[1]/'docs/g2/verification'
    path=tmp_path/'legacy.g1.sqlite'
    path.write_bytes(gzip.decompress((fixture/'legacy-active.g1.gz').read_bytes()))
    raw=path.read_bytes();w=load_game(path)
    assert path.read_bytes()==raw
    assert w.digest()==json.loads((fixture/'legacy-active.json').read_text())['digest']
    v=GodObserver(w,paused=True)
    try:
        v.draw();v.handle([key(pygame.K_PAGEUP),key(pygame.K_F2)]);v.draw()
        assert path.read_bytes()==raw
        before=w.state();save_game(w,tmp_path/'roundtrip.g1.sqlite')
        loaded=load_game(tmp_path/'roundtrip.g1.sqlite')
        assert loaded.state()==before
        loaded.step(25);w.step(25);assert loaded.state()==w.state()
    finally:pygame.quit()
