"""Camera, honest presentation and actual displayed-hit integration tests."""
import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
from functools import partial
import time

import pygame
import pytest
from gnome_fortress.camera import Camera
from gnome_fortress.pixel_art import appearance,gnome_sprite,terrain_tile,TERRAIN_COLORS
from gnome_fortress.living_viewer import LivingObserver,NEEDS,happening
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.god_viewer import run
from gnome_fortress.model import Event


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
def click(pos):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)


@pytest.fixture
def view():
    world=TerrainWorld(1);v=LivingObserver(world,paused=True,window_size=(1280,720));v.draw()
    yield v
    pygame.quit()


@pytest.mark.parametrize('viewport',[(12,110,892,465),(12,110,300,200),(12,110,3000,1600)])
def test_camera_roundtrip_edges_clamp_and_zoom_limits(viewport):
    c=Camera(48,32,viewport,24)
    for _ in range(30):c.zoom(1)
    assert c.tile==96
    c.pan(100000,-100000)
    assert c.x<=48-c.viewport.w/c.tile if c.viewport.w/c.tile<48 else c.x<0
    for _ in range(50):c.zoom(-1)
    assert c.tile==c.minimum
    c.fit();x0,y0,x1,y1=c.visible_bounds()
    assert 0<=x0<x1<=48 and 0<=y0<y1<=32
    for y in range(y0,y1):
        for x in range(x0,x1):
            rect=c.tile_rect(x,y)
            if c.viewport.collidepoint(rect.center):assert c.screen_to_world(rect.center)==(x,y)
    assert c.screen_to_world((c.viewport.right,c.viewport.bottom)) is None


def test_zoom_anchor_and_pixel_inverse():
    c=Camera(200,100,(12,107,892,465),24);anchor=(407,313)
    before=c.screen_to_world(anchor);c.zoom(2,anchor)
    assert c.screen_to_world(anchor)==before
    c.pan(43,-37)
    for x,y in ((80,40),(100,50),(120,55)):
        rect=c.tile_rect(x,y)
        if c.viewport.collidepoint(rect.center):assert c.screen_to_world(rect.center)==(x,y)


@pytest.mark.parametrize('power,k',[('rain',pygame.K_r),('drought',pygame.K_d),('rupture',pygame.K_e),('rewild',pygame.K_f),('wellspring',pygame.K_p)])
def test_all_powers_target_exact_transformed_tile_and_preview(view,power,k):
    v=view;w=v.world;v.camera.zoom(2);v.camera.pan(87,49);v.camera.center_tile(24,16)
    pos=v.camera.tile_rect(24,16).center;v.handle([key(k),pygame.event.Event(pygame.MOUSEMOTION,pos=pos)])
    cells=v.preview_cells();assert cells and v.hover==(24,16)
    before=w.rng.getstate();v.draw();v.handle([click(pos)])
    p=w.interventions[-1]
    assert p.kind==power and (p.x,p.y)==(24,16) and p.status=='queued'
    assert {(x,y) for x,y,eligible in cells}==set(w.footprint(p))
    assert w.rng.getstate()==before
    assert all((x-24)**2+(y-16)**2<=p.radius**2 for x,y,eligible in cells)


def test_edges_and_hud_cannot_cast_hidden_target(view):
    v=view;v.handle([key(pygame.K_e)]);v.draw()
    for rect,label in v.toolbar.values():
        if label.startswith('Rupture'):v.handle([click(rect.center)])
    assert not v.world.interventions
    for x,y in [(0,0),(47,31)]:
        v.camera.center_tile(x,y);pos=v.camera.tile_rect(x,y).center
        assert v.viewport.collidepoint(pos);v.handle([click(pos)])
        assert (v.world.interventions[-1].x,v.world.interventions[-1].y)==(x,y)
    count=len(v.world.interventions);v.handle([key(pygame.K_a),click(v.viewport.center)])
    assert len(v.world.interventions)==count
    v.handle([key(pygame.K_a),key(pygame.K_t),click(v.camera.tile_rect(47,31).center)])
    assert len(v.world.interventions)==count and v.tile_xy==(47,31)


def test_crowd_visible_alpha_pick_and_repeated_click_cycle():
    w=TerrainWorld()
    for a in w.living():a.x,a.y=20,10
    v=LivingObserver(w,paused=True,window_size=(1280,720))
    try:
        before=w.state();v.camera.zoom(2);v.camera.center_tile(20,10);v.draw();items,_=v.sprite_layout()
        front=items[-1];identity,image,mask,rect=front
        local=next((x,y) for y in range(mask.get_size()[1]) for x in range(mask.get_size()[0]) if mask.get_at((x,y)))
        pos=(rect.x+local[0],rect.y+local[1]);v.handle([click(pos)])
        assert v.selected==identity
        for _ in range(12):
            previous=v.selected;v.draw();v.handle([click(pos)])
            assert v.selected==previous%60+1
        assert v.selected in [i for i,_,_,_ in v.sprite_layout()[0]]
        assert len(v.sprite_layout()[0])==9 and w.state()==before
    finally:pygame.quit()


def test_stable_cosmetics_sleep_and_no_rng(view,tmp_path):
    v=view;a=v.world.agents[1];before=v.world.rng.getstate()
    style=appearance(a.id);awake,_=gnome_sprite(style,False,64);sleep,_=gnome_sprite(style,True,64)
    assert pygame.image.tobytes(awake,'RGBA')!=pygame.image.tobytes(sleep,'RGBA')
    path=tmp_path/'look.g5.sqlite';save_game(v.world,path);loaded=load_game(path)
    assert appearance(loaded.agents[1].id)==style and loaded.state()==v.world.state()
    assert appearance(a.id)==appearance(a.id) and v.world.rng.getstate()==before
    for kind in TERRAIN_COLORS:assert terrain_tile(kind,0,24).get_size()==(24,24)
    assert len({pygame.image.tobytes(terrain_tile(k,0,24),'RGB') for k in TERRAIN_COLORS})==5


def test_follow_sleep_pan_death_watch_identity(view):
    v=view;w=v.world;a=w.agents[1];v.handle([key(pygame.K_w),key(pygame.K_c)])
    assert v.follow_id==v.watch_id==v.selected==1
    a.sleep_until=100;v.sync();assert v.follow_id==1
    v.handle([key(pygame.K_LEFT)]);assert v.follow_id is None and v.selected==1
    v.handle([key(pygame.K_c)]);w.step();v.sync();assert v.follow_id==1
    w.kill(a,'controlled UI fixture');before=w.state();v.draw()
    assert v.selected==v.watch_id==1 and v.follow_id is None and 'died' in v.follow_note
    v.handle([key(pygame.K_c)]);assert v.follow_id is None and w.state()==before


def test_event_navigation_family_and_missing_records(view):
    v=view;w=v.world;child=w._spawn(12,12,w.agents[1].traits,(1,2));v.sync()
    event=w.events[-1];v.open_event(event)
    assert v.selected==child.id and v.tab=='life' and 'not recorded' in v.notice
    v.navigate('family');v.draw()
    parent=next(rect for rect,name in v.ui_hits if name=='member:1');v.handle([click(parent.center)])
    assert v.selected==1 and v.tab=='gnome'
    v.camera.zoom(3) # Allow true centering; near-edge low zoom correctly clamps.
    hazard=Event(w.tick,'hazard',child.id,None,{'x':12,'y':12,'damage':9});v.open_event(hazard)
    assert v.selected==child.id and v.camera.screen_to_world(v.viewport.center)==(12,12)
    v.open_event(Event(1,'death',99999,None,{}));v.draw();assert 'unavailable' in v.notice
    v.selected=99999;v.draw();v.handle([key(pygame.K_c)]);assert v.follow_id is None


@pytest.mark.parametrize('size',[(800,600),(1280,720),(1920,1080),(3840,2160)])
def test_responsive_bounds_and_modal_choices(size):
    w=TerrainWorld();v=LivingObserver(w,paused=True,window_size=size)
    try:
        v.draw();v.inspector_open=True;v.layout(size);v.draw()
        bounds=v.screen.get_rect()
        assert bounds.contains(v.viewport) and bounds.contains(v.panel_rect)
        assert not v.viewport.colliderect(v.panel_rect) and not v.viewport.colliderect(v.event_rect)
        for rect,label in v.toolbar.values():assert bounds.contains(rect)
        v.advisor.start();v.advisor.text='A long factual reply. '*100;v.draw()
        choices=[r for r,name in v.ui_hits if name.startswith('advisor:')]
        assert len(choices)==6 and all(v.body.contains(r) for r in choices)
        old=v.camera.tile;v.handle([pygame.event.Event(pygame.MOUSEWHEEL,y=-1,pos=v.panel_rect.center)])
        assert v.camera.tile==old
    finally:pygame.quit()


def test_needs_actual_ranges_and_negative_final_health(view):
    v=view;a=v.world.agents[1];v.world.kill(a,'controlled UI fixture');a.health=-3;a.hunger=147;a.thirst=149;a.fatigue=124
    labels=[];original=v.label
    def record(text,*args,**kwargs):labels.append(str(text));return original(text,*args,**kwargs)
    v.label=record;before=v.world.state();v.draw()
    assert any('Health -3 / 100' in s for s in labels)
    assert any('Hunger 147' in s and '150' in s for s in labels)
    assert any('Fatigue 124' in s and '130' in s for s in labels)
    assert any('Final stored' in s for s in labels) and v.world.state()==before
    assert {key:maximum for key,label,maximum,high_bad in NEEDS}=={'health':100,'hunger':150,'thirst':150,'fatigue':130}


def test_draw_navigation_cadence_readonly_reference(view):
    v=view;a=v.world;initial=a.state();rng=a.rng.getstate()
    for k in (pygame.K_c,pygame.K_c,pygame.K_RIGHT,pygame.K_b,pygame.K_h,pygame.K_F3,pygame.K_w):v.handle([key(k)]);v.draw()
    assert a.state()==initial and a.rng.getstate()==rng
    for tick in range(40):
        if tick in (0,9,20):
            for world in (a,):world.request({0:'rain',9:'rupture',20:'rewild'}[tick],20,10)
        v.handle([key(pygame.K_PERIOD)]);v.advance(0)
        for _ in range(tick%3):v.draw()
    # Replay identical commands from scratch with no presentation.
    b=TerrainWorld(1)
    for tick in range(40):
        if tick in (0,9,20):b.request({0:'rain',9:'rupture',20:'rewild'}[tick],20,10)
        b.step()
    assert a.state()==b.state() and a.rng.getstate()==b.rng.getstate()


def test_long_indexes_not_rescanned_and_history_previews(view):
    v=view;w=v.world;w.step(300);v.draw();v.navigate('life');v.draw()
    counts=(v.presentation.events.records_examined,v.presentation.land.records_examined,v.life.records_examined)
    before=w.state()
    for _ in range(8):v.draw();v.browse_events(1)
    assert counts==(v.presentation.events.records_examined,v.presentation.land.records_examined,v.life.records_examined)
    assert w.state()==before
    v.handle([key(pygame.K_e)]);v.camera.center_tile(20,10);pos=v.camera.tile_rect(20,10).center
    v.handle([click(pos),key(pygame.K_PERIOD)]);v.advance(0);v.sync()
    v.handle([key(pygame.K_t),click(pos)]);v.draw()
    assert v.tab=='terrain' and v.tile_xy==(20,10) and v.presentation.land.by_tile


def slow_save(world,path):time.sleep(.25);return save_game(world,path)


def test_new_view_runs_during_detached_save_and_flushes(tmp_path):
    w=TerrainWorld();path=tmp_path/'new-ui.g5.sqlite';instances=[]
    class Inspector(LivingObserver):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.save_requested=True;self.tested=False;instances.append(self)
        def handle(self,events):
            super().handle(events)
            if getattr(self,'checkpoint_pending',False) and not self.tested:
                assert not self.saving;self.tested=True
                super().handle([key(pygame.K_c),key(pygame.K_b),key(pygame.K_F3),key(pygame.K_PERIOD)])
            if self.notice.startswith('Saved tick'):self.running=False
    run(w,path,slow_save,paused=True,max_frames=100,observer_class=Inspector,worker_class=TerrainCheckpointWorker)
    assert instances[0].tested and w.tick==1 and load_game(path).tick==0
    save_game(w,path);assert load_game(path).state()==w.state()


def test_scroll_routing_disarm_modal_and_drag_do_not_change_rng(view):
    v=view;w=v.world;w.step(100);v.draw();before=w.state();rng=w.rng.getstate()
    tile=v.camera.tile
    v.handle([pygame.event.Event(pygame.MOUSEWHEEL,y=1,pos=v.event_rect.center)])
    assert v.event_offset>0 and v.camera.tile==tile
    v.navigate('life');v.draw();v.life_tail=False;v.life_start=0
    v.handle([pygame.event.Event(pygame.MOUSEWHEEL,y=-1,pos=v.body.center)])
    assert v.camera.tile==tile
    v.handle([key(pygame.K_e),key(pygame.K_a),click(v.viewport.center)])
    assert not w.interventions and v.mode is None
    v.handle([key(pygame.K_a),key(pygame.K_e),key(pygame.K_F3),click(v.viewport.center)])
    assert not w.interventions and v.mode is None
    v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=2,pos=v.viewport.center),
              pygame.event.Event(pygame.MOUSEMOTION,pos=v.viewport.center,rel=(30,20)),
              pygame.event.Event(pygame.MOUSEBUTTONUP,button=2,pos=v.viewport.center)])
    assert not v.dragging and v.follow_id is None
    assert w.state()==before and w.rng.getstate()==rng


def test_clicked_selected_label_and_dead_marker_are_not_hidden_agents(view):
    v=view;v.camera.zoom(3);v.center_selected();v.draw()
    tag=v.selection_tag(v.sprite_layout()[0]);v.handle([click(tag[0].center)])
    assert v.selected==1
    v.world.kill(v.world.agents[1],'controlled UI fixture');v.draw();tag=v.selection_tag(v.sprite_layout()[0])
    v.handle([click(tag[0].center)]);assert v.selected==1 and v.tab=='life' and v.follow_id is None


def test_live_launcher_uses_new_view_without_changing_checkpoint(tmp_path):
    import subprocess,sys,json
    path=tmp_path/'launcher.g5.sqlite'
    command=[sys.executable,'-m','gnome_fortress.god_world','--db',str(path),'--paused','--frames','2','--capture',str(tmp_path/'frame.png')]
    result=subprocess.run(command,capture_output=True,text=True,timeout=10,check=True)
    saved=load_game(path);assert saved.state()==TerrainWorld(1).state()
    surface=pygame.image.load(str(tmp_path/'frame.png'))
    assert surface.get_width()>=800 and surface.get_height()>=600
    assert json.loads(result.stdout.splitlines()[-1])['tick']==0


def test_collapsing_advisor_does_not_leave_invisible_modal(view):
    v=view;before=v.world.state();v.action('advisor');v.draw()
    assert v.advisor.open and v.inspector_open
    v.action('inspector');v.draw();assert not v.inspector_open and not v.advisor.open
    x0,y0,x1,y1=v.camera.visible_bounds()
    xy=next((x,y) for y in range(y0,y1) for x in range(x0,x1) if not v.occupants.get((x,y)) and v.viewport.collidepoint(v.camera.tile_rect(x,y).center))
    v.handle([click(v.camera.tile_rect(*xy).center)])
    assert v.tab=='terrain' and v.tile_xy==xy and v.world.state()==before
