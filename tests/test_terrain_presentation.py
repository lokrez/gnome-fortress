import copy
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
import pytest
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_viewer import TerrainObserver
from gnome_fortress.terrain_presentation import TerrainIndex,TerrainPresentation
from gnome_fortress.model import Event
from gnome_fortress.runtime import CheckpointWorker


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
def click(pos):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)


def test_incremental_index_unique_currently_altered_and_pages():
    w=TerrainWorld();xy=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain=='forest')
    index=TerrainIndex(w);initial=index.records_examined
    for kind in ('rupture','rewild','rupture','rewild'):
        w.request(kind,*xy,0);w.step();index.update()
    assert index.summary()['transitions']==4 and len(index.by_tile)==1
    assert index.summary()['currently_altered']==0 and index.summary()['ever_transformed']==1
    assert [p.kind for p,c in index.page(xy,1,2)]==['rewild','rupture']
    examined=index.records_examined;transitions=index.transitions_examined
    for _ in range(10):index.update();index.page(xy,0,1)
    assert index.records_examined==examined and index.transitions_examined==transitions
    # Attribution uses the recorded coordinates and hazard-time terrain, not proximity.
    assert index.hazard_provenance(Event(1,'hazard',1,None,dict(x=xy[0],y=xy[1],damage=12)))==1
    assert index.hazard_provenance(Event(2,'hazard',1,None,dict(x=xy[0],y=xy[1],damage=12))) is None
    assert index.hazard_provenance(Event(3,'hazard',1,None,dict(x=xy[0],y=xy[1],damage=12)))==3
    assert index.hazard_provenance(Event(3,'hazard',1,None,dict(damage=12))) is None


def test_all_controls_previews_history_and_advisor_navigation():
    w=TerrainWorld();v=TerrainObserver(w,paused=True);v.watch_id=1
    try:
        before=w.state();v.draw();assert w.state()==before
        for k,name,r in [(pygame.K_e,'rupture',2),(pygame.K_f,'rewild',2),(pygame.K_p,'wellspring',0)]:
            v.handle([key(k),pygame.event.Event(pygame.MOUSEMOTION,pos=(2*v.tile+1,2*v.tile+1))])
            assert v.mode==name and v.preview_radius()==r
            cells=v.preview_cells()
            assert all((x-2)**2+(y-2)**2<=r*r for x,y,eligible in cells)
            assert all(eligible==(w.cell(x,y).terrain in {'rupture':('grass','forest'),'rewild':('hazard',),'wellspring':('rock',)}[name]) for x,y,eligible in cells)
            v.draw()
        v.handle([key(pygame.K_e),click((2*v.tile+1,2*v.tile+1))]);assert w.interventions[-1].status=='queued'
        v.handle([key(pygame.K_PERIOD)]);v.advance(0);assert w.interventions[-1].status=='completed'
        v.handle([key(pygame.K_f),click((2*v.tile+1,2*v.tile+1)),key(pygame.K_PERIOD)]);v.advance(0)
        v.handle([key(pygame.K_t),click((2*v.tile+1,2*v.tile+1))]);v.draw()
        assert v.tab=='terrain' and len(v.presentation.land.by_tile[(2,2)])==2
        v.handle([key(pygame.K_a),key(pygame.K_5)]);v.draw()
        assert 'historical transitions' in v.advisor.text
        assert 'Rupture: 1 requests' in v.advisor.text
        v.handle([key(pygame.K_2)]);assert v.tab=='terrain' and not v.advisor.open
        assert v.watch_id==v.selected==1
        v.handle([key(pygame.K_F3)]);v.draw();assert v.tab=='life' and not v.tile_select
        v.handle([key(pygame.K_a),key(pygame.K_3),key(pygame.K_2)]);assert 'One-shot' in v.advisor.text
        v.handle([key(pygame.K_a),key(pygame.K_o)]);assert v.mode is None
    finally:pygame.quit()


def test_saving_cast_guard_and_responsive_readonly_inspection(tmp_path):
    import threading
    w=TerrainWorld();v=TerrainObserver(w,paused=True);ready=threading.Event();release=threading.Event()
    from gnome_fortress.terrain_storage import save_game,load_game
    def gated_save(world,path):
        ready.set();release.wait(5);return save_game(world,path)
    worker=CheckpointWorker(gated_save)
    try:
        path=tmp_path/'pending.g5.sqlite';worker.start(w,path);assert ready.wait(2);v.saving=worker.pending;before=w.state()
        for k in (pygame.K_e,pygame.K_f,pygame.K_p,pygame.K_r,pygame.K_d):
            v.handle([key(k),click((2*v.tile+1,2*v.tile+1))]);v.advance(1)
        v.handle([key(pygame.K_t),click((2*v.tile+1,2*v.tile+1)),key(pygame.K_a),key(pygame.K_5)]);v.draw()
        assert w.state()==before and not w.interventions and v.advisor.open
        assert 'Saving' in v.notice
        release.set();worker.close();assert load_game(path).state()==before
    finally:release.set();worker.close();pygame.quit()


def test_cadence_and_older_tile_page_anchor_missing_history():
    a=TerrainWorld(2);b=TerrainWorld(2);v=TerrainObserver(a,paused=True)
    try:
        for tick in range(40):
            if tick%3==0:
                kind='rupture' if tick%2==0 else 'rewild'
                for w in (a,b):w.request(kind,2,2,0)
            a.step();b.step()
            v.handle([key(pygame.K_t)] if tick==0 else [])
            for _ in range(tick%4):v.draw()
        assert a.state()==b.state()
        v.tile_xy=(2,2);v.tab='terrain';v.browse_tile(-999);v.draw();start=v.tile_start
        a.request('rupture',2,2,0);a.step();v.draw()
        assert not v.tile_tail and v.tile_start==start
        v.tile_xy=(3,3);v.draw();assert not v.presentation.land.page((3,3))
    finally:pygame.quit()


def test_event_feed_terrain_and_no_per_frame_historical_scan():
    w=TerrainWorld()
    for _ in range(12):w.request('rupture',2,2,0);w.step();w.request('rewild',2,2,0);w.step()
    v=TerrainObserver(w,paused=True)
    try:
        v.handle([key(pygame.K_t)]);v.tile_xy=(2,2);v.draw()
        event_scans=v.presentation.events.records_examined;land_scans=v.presentation.land.records_examined
        for _ in range(20):v.draw()
        assert v.presentation.events.records_examined==event_scans and v.presentation.land.records_examined==land_scans
        feed=v.presentation.events.page(count=10000)
        assert sum(e.kind=='divine_terrain' for _,e in feed)==24
        event=next(e for _,e in feed if e.kind=='divine_terrain')
        assert 'completed' in v.format_event(event)
    finally:pygame.quit()


def test_empty_land_dialogue_and_small_window_buttons():
    w=TerrainWorld();v=TerrainObserver(w,paused=True)
    try:
        v.screen=pygame.display.set_mode((v.map_width+470,600))
        for topic in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4,pygame.K_5):
            v.advisor.start();v.handle([key(topic)]);v.draw()
            assert all(r.bottom<582 for r,_ in v.advisor_hits)
        v.advisor.start();v.handle([key(pygame.K_5),key(pygame.K_1)]);assert 'No terrain action' in v.advisor.text
        before=w.state();v.handle([key(pygame.K_0),key(pygame.K_0)]);assert not v.advisor.open
        assert w.state()==before
        v.advisor.start();v.draw();assert len(v.advisor_hits)==6 and all(r.bottom<582 for r,_ in v.advisor_hits)
    finally:pygame.quit()
