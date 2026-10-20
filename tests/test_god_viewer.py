import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import json
import subprocess
import sys
import threading

import pygame

from gnome_fortress.game import GameWorld
from gnome_fortress.god_viewer import GodObserver,run
from gnome_fortress.game_storage import load_game


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
def click(x,y):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(x,y))


def test_observe_preview_pause_and_inspection_do_not_mutate():
    w=GameWorld();v=GodObserver(w,paused=True)
    try:
        initial=w.state()
        v.handle([key(pygame.K_r),pygame.event.Event(pygame.MOUSEMOTION,pos=(50,70)),key(pygame.K_PLUS)])
        v.draw();v.advance(3)
        v.handle([key(pygame.K_o),key(pygame.K_TAB),click(25,25)])
        v.draw();assert w.state()==initial
        v.handle([key(pygame.K_PERIOD)]);v.advance(0)
        reference=GameWorld();reference.step()
        assert w.state()==reference.state()
    finally:pygame.quit()


def test_cast_controls_repeated_clicks_edge_and_save_lock():
    w=GameWorld();v=GodObserver(w,paused=True)
    try:
        v.handle([click(v.buttons['rain'].centerx,v.buttons['rain'].centery),click(0,0),click(0,0)])
        assert len(w.interventions)==2 and all(p.activation_tick==1 for p in w.interventions)
        v.saving=True;v.handle([click(0,0)]);assert len(w.interventions)==2
        v.saving=False
        v.handle([key(pygame.K_d),click(v.map_width-1,w.height*v.tile-1),click(-1,0)])
        assert len(w.interventions)==3 and w.interventions[-1].x==w.width-1
        v.handle([key(pygame.K_PERIOD)]);v.advance(0);v.draw()
        assert w.tick==1 and all(p.status=='active' for p in w.interventions)
        v.handle([click(v.buttons['observe'].centerx,v.buttons['observe'].centery)])
        assert v.mode is None
    finally:pygame.quit()


def test_render_cadence_does_not_affect_scheduled_outcomes():
    a,b=GameWorld(8),GameWorld(8);v=GodObserver(a,paused=True)
    try:
        for w in (a,b):w.request('rain',0,0,5,35)
        for tick in range(40):
            v.handle([key(pygame.K_PERIOD)]);v.advance(0)
            for _ in range(tick%3):v.draw()
        b.step(40);assert a.state()==b.state()
        for g in list(a.living()):a.kill(g,'test')
        ended=a.state();v.handle([key(pygame.K_SPACE),key(pygame.K_PERIOD)]);v.advance(100);v.draw()
        assert a.state()==ended and v.paused
    finally:pygame.quit()


def test_worker_freezes_casts_and_ticks_but_services_inspection(tmp_path,monkeypatch):
    from gnome_fortress import god_viewer
    release=threading.Event();seen=[];w=GameWorld()
    class Inspector(GodObserver):
        def __init__(self,*args,**kw):super().__init__(*args,**kw);self.save_requested=True
        def handle(self,events):
            super().handle(events)
            if self.saving:
                super().handle([key(pygame.K_TAB),key(pygame.K_r),click(0,0)])
                seen.append(self.selected);release.set();self.running=False
    def writer(world,path):
        assert release.wait(2)
        assert world.tick==0 and not world.interventions
        return {'tick':world.tick}
    monkeypatch.setattr(god_viewer,'GodObserver',Inspector)
    run(w,tmp_path/'x.g1.sqlite',writer,paused=True,max_frames=30)
    assert seen and seen[0]==2


def test_cli_shutdown_resume_and_corruption_no_fallback(tmp_path):
    path=tmp_path/'cli.g1.sqlite'
    cmd=[sys.executable,'-m','gnome_fortress.god_demo','--db',str(path)]
    env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    first=subprocess.run(cmd+['--paused','--frames','2'],env=env,capture_output=True,text=True,check=True)
    assert json.loads(first.stdout)['tick']==0
    second=subprocess.run(cmd+['--headless','--ticks','10'],env=env,capture_output=True,text=True,check=True)
    assert json.loads(second.stdout)['tick']==10 and load_game(path).tick==10
    before=path.read_bytes()
    rejected=subprocess.run(cmd+['--new','--headless'],env=env,capture_output=True)
    assert rejected.returncode and path.read_bytes()==before
    path.write_bytes(b'broken checkpoint');before=path.read_bytes()
    bad=subprocess.run(cmd+['--headless'],env=env,capture_output=True)
    assert bad.returncode and path.read_bytes()==before and b'Cannot open' in bad.stderr


def test_sigterm_preserves_active_checkpoint_on_clean_shutdown(tmp_path):
    import signal,time
    from gnome_fortress.game_storage import save_game
    w=GameWorld();w.request('rain',2,2);w.step(2)
    path=tmp_path/'signal.g1.sqlite';save_game(w,path)
    process=subprocess.Popen([sys.executable,'-m','gnome_fortress.god_demo','--db',str(path),'--paused'],
        env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        time.sleep(1)
        assert process.poll() is None
        process.send_signal(signal.SIGTERM)
        stdout,stderr=process.communicate(timeout=5)
        assert process.returncode==0,(stdout,stderr)
        assert load_game(path).state()==w.state()
    finally:
        if process.poll() is None:process.kill();process.wait()
