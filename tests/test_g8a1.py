"""Folklore art is reproducible presentation, not a model extension."""
import os
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
import pytest
from gnome_fortress.pixel_art import (appearance,gnome_native,gnome_sprite,terrain_native,
    terrain_decoration,death_portrait,icon,journal_panel,TERRAIN_COLORS,HAT_PATHS)
from gnome_fortress.living_viewer import LivingObserver,POWER_INK,happening,event_glyph
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.model import Event


def pixels(s):return pygame.image.tobytes(s,'RGBA')


def test_eight_silhouettes_and_native_bounds():
    assert len(HAT_PATHS)==8
    masks=[]
    for i in range(8):
        s=gnome_native(appearance(i));assert s.get_size()==(32,40)
        m=pygame.mask.from_surface(s);masks.append(m)
        assert m.count()>200 and s.get_bounding_rect().w<=32 and s.get_bounding_rect().h<=40
    assert len({pixels(gnome_native(appearance(i))) for i in range(8)})==8
    # Real shape differences: alpha silhouettes, not just differently colored pixels.
    assert all(masks[i].count()!=masks[j].count() or masks[i].overlap_area(masks[j],(0,0))!=masks[i].count()
               for i in range(8) for j in range(i))
    for kind in TERRAIN_COLORS:assert terrain_native(kind,0).get_size()==(32,32)


def test_sleep_walk_archival_and_exact_scaled_alpha():
    for i in range(8):
        style=appearance(i)
        assert pixels(gnome_native(style,False,0))!=pixels(gnome_native(style,False,1))
        assert gnome_native(style,True).get_size()==(40,32)
        for size in (10,24,48,86):
            s,m=gnome_sprite(style,False,size)
            assert s.get_height()==size and m.get_size()==s.get_size()
            assert pygame.mask.from_surface(s).count()==m.count()
    assert pixels(death_portrait(40))!=pixels(gnome_native(appearance(1)))


def test_art_is_stable_across_reload_cache_cadence(tmp_path):
    w=TerrainWorld(1);before=w.state();rng=w.rng.getstate()
    images={i:pixels(gnome_sprite(appearance(i),False,64)[0]) for i in range(1,61)}
    path=tmp_path/'art.g5.sqlite';save_game(w,path);loaded=load_game(path)
    gnome_sprite.cache_clear();gnome_native.cache_clear()
    for i in reversed(list(loaded.agents)):
        for _ in range(i%3+1):assert images[i]==pixels(gnome_sprite(appearance(i),False,64)[0])
    assert loaded.state()==before and w.rng.getstate()==rng


def test_provenance_overlays_require_real_history_and_share_edge_keys():
    n=('grass','water','rock','forest')
    plain=terrain_decoration('grass',n,None,32)
    for power in ('rupture','rewild','wellspring'):
        assert pixels(plain)!=pixels(terrain_decoration('grass',n,power,32))
    # Different neighboring terrain with the same boundary pattern shares artwork.
    assert terrain_decoration('grass',n,None,32) is terrain_decoration('grass',('grass','rock','hazard','water'),None,32)
    assert len({pixels(icon(k,20)) for k in ('rain','drought','rupture','rewild','wellspring')})==5
    assert journal_panel(320,600).get_size()==(320,600)


@pytest.mark.parametrize('size',[(800,600),(1280,720),(1920,1080),(3840,2160)])
def test_journal_controls_and_readonly_dense_selection(size):
    w=TerrainWorld(2)
    # Explicit rendering fixture; positions are not presented as natural behavior.
    for a in w.living():a.x,a.y=20,10
    v=LivingObserver(w,paused=True,window_size=size)
    try:
        v.inspector_open=True;v.layout(size);v.camera.tile=64;v.camera.clamp();v.camera.center_tile(20,10)
        before=w.state();rng=w.rng.getstate();v.draw()
        assert v.screen.get_rect().contains(v.body)
        items,_=v.sprite_layout();assert len(items)==9 and items[-1][0]==v.selected
        identity,image,mask,rect=items[-1]
        # Use a real opaque pixel in the hat; appearance and hit mask agree.
        xy=next((x,y) for y in range(mask.get_size()[1]) for x in range(mask.get_size()[0]) if mask.get_at((x,y)))
        pos=(rect.x+xy[0],rect.y+xy[1]);assert v.viewport.collidepoint(pos)
        assert v.pick_gnome(pos) and v.selected==identity
        for power in POWER_INK:
            v.set_mode(power);v.pointer=v.camera.tile_rect(20,10).center;v.draw()
            assert v.hover==(20,10) and 'ARMED' in v.notice
        assert w.state()==before and w.rng.getstate()==rng
        w.kill(w.agents[identity],'controlled art test');before=w.state();v.selected=identity;v.set_mode(None)
        v.draw();assert w.state()==before
    finally:pygame.quit()


def test_no_invented_icon_event_content():
    w=TerrainWorld()
    assert event_glyph(Event(4,'divine_terrain',None,None,{}),w)=='divine'
    w.request('rewild',10,10);w.step()
    assert event_glyph(next(e for e in w.events if e.kind=='divine_terrain'),w)=='rewild'
    assert 'cause unavailable' in happening(Event(4,'death',1,None,{}),w)
    assert 'injured on hazardous terrain' in happening(Event(4,'hazard',1,None,{'damage':7}),w)
    assert not any(word in happening(w.events[0],w).lower() for word in ('friend','religion','occupation','grief'))


def test_window_manager_constrained_size_uses_actual_surface(monkeypatch):
    original=pygame.display.set_mode
    def constrained(size,*args,**kwargs):
        actual=(size[0],size[1]-60) if size==(1280,720) else size
        return original(actual,*args,**kwargs)
    monkeypatch.setattr(pygame.display,'set_mode',constrained)
    v=LivingObserver(TerrainWorld(),paused=True,window_size=(1280,720))
    try:
        v.draw();assert v.screen.get_size()==(1280,660)
        assert v.screen.get_rect().contains(v.panel_rect)
        assert v.screen.get_rect().contains(v.event_rect)
        v.handle([pygame.event.Event(pygame.VIDEORESIZE,w=1280,h=720)])
        assert v.screen.get_rect().contains(v.panel_rect)
    finally:pygame.quit()


def test_composed_tiles_match_source_art_without_alpha_blend_each_frame():
    from gnome_fortress.pixel_art import illustrated_tile,terrain_tile
    for kind in TERRAIN_COLORS:
        for history in (None,'rupture','rewild','wellspring'):
            expected=terrain_tile(kind,2,64).copy()
            expected.blit(terrain_decoration(kind,('grass','rock','water','forest'),history,64),(0,0))
            edges=sum(1<<i for i,k in enumerate(('grass','rock','water','forest')) if k!=kind)
            actual=illustrated_tile(kind,2,edges,history,64)
            assert not actual.get_flags() & pygame.SRCALPHA
            assert pixels(actual)==pixels(expected)


def test_viewer_history_art_uses_objective_last_transition_only():
    w=TerrainWorld(1);v=LivingObserver(w,paused=True,window_size=(1280,720))
    try:
        xy=next((x,y) for y in range(w.height) for x in range(w.width) if w.cell(x,y).terrain=='forest')
        assert xy not in v.presentation.land.by_tile
        w.request('rupture',*xy);w.step();w.request('rewild',*xy);w.step();v.sync()
        history=v.presentation.land.by_tile[xy]
        assert [w.interventions[i-1].kind for i,c in history]==['rupture','rewild']
        v.camera.tile=64;v.camera.clamp();v.camera.center_tile(*xy)
        before=w.state();v.draw();enabled=pixels(v.screen)
        v.footprints=False;v.draw();assert enabled!=pixels(v.screen)
        assert w.state()==before and len(history)==2
    finally:pygame.quit()
