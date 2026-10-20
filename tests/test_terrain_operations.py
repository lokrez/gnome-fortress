"""Operational failure cases for the separate launcher/shared writer loop."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import json
import signal
import subprocess
import sys
import time

import pygame
from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import save_game as save_legacy
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_viewer import TerrainObserver
from gnome_fortress.god_viewer import run


def test_new_cli_import_resume_rejection_no_reseed(tmp_path):
    src=tmp_path/'old.g1.sqlite';a=GameWorld(1);a.step(9);a.request('rain',2,2);a.step()
    save_legacy(a,src);raw=src.read_bytes();dst=tmp_path/'new.g5.sqlite'
    command=[sys.executable,'-m','gnome_fortress.god_world','--db',str(dst)]
    imported=subprocess.run(command+['--import-legacy',str(src),'--headless','--ticks','0'],capture_output=True,text=True,check=True)
    assert json.loads(imported.stdout)['tick']==10 and src.read_bytes()==raw
    assert World.state(load_game(dst))==World.state(a)
    subprocess.run(command+['--headless','--ticks','20'],capture_output=True,check=True);a.step(20)
    assert World.state(load_game(dst))==World.state(a)
    for extra in (['--new'],['--import-legacy',str(src)]):
        before=dst.read_bytes();bad=subprocess.run(command+extra+['--headless','--ticks','0'],capture_output=True)
        assert bad.returncode and dst.read_bytes()==before
    dst.write_bytes(b'corrupt');bad=subprocess.run(command+['--headless','--ticks','0'],capture_output=True)
    assert bad.returncode and b'Cannot open' in bad.stderr and dst.read_bytes()==b'corrupt'
    assert src.read_bytes()==raw


def test_real_interrupted_sqlite_writer_keeps_last_commit(tmp_path):
    path=tmp_path/'crash.g5.sqlite';w=TerrainWorld();w.request('rupture',2,2);w.step();save_game(w,path)
    script="""import os,sqlite3,sys
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA synchronous=FULL');c.execute('BEGIN IMMEDIATE')
c.execute("UPDATE game_checkpoint SET payload='incomplete',sha256='bad'");os._exit(7)
"""
    result=subprocess.run([sys.executable,'-c',script,str(path)])
    assert result.returncode==7 and load_game(path).state()==w.state()


def test_terrain_sigterm_clean_shutdown(tmp_path):
    path=tmp_path/'signal.g5.sqlite';w=TerrainWorld();w.request('rupture',2,2);w.request('rain',2,2);w.step(3);save_game(w,path)
    process=subprocess.Popen([sys.executable,'-m','gnome_fortress.god_world','--db',str(path),'--paused'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        time.sleep(1);assert process.poll() is None;process.send_signal(signal.SIGTERM)
        out,err=process.communicate(timeout=6)
        assert process.returncode==0,(out,err)
        assert load_game(path).state()==w.state()
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_failed_terrain_autosave_stays_suppressed_until_explicit_retry(tmp_path,monkeypatch):
    calls=[];instances=[]
    class FastClock:
        def tick(self,hz):time.sleep(.01);return 0
    class Inspector(TerrainObserver):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.retried=False;self.started=False;instances.append(self)
        def handle(self,events):
            super().handle(events)
            if not self.started:self.world.step();self.started=True
            if 'Save failed' in self.notice and not self.retried:
                assert len(calls)==1;self.retried=True
                super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_s)])
            elif 'Saved tick' in self.notice:self.running=False
    def writer(world,path):
        calls.append(world.tick)
        if len(calls)==1:raise OSError('controlled test failure')
        return save_game(world,path)
    monkeypatch.setattr(pygame.time,'Clock',FastClock)
    w=TerrainWorld();expected=TerrainWorld();expected.step();before=expected.state();path=tmp_path/'retry.g5.sqlite'
    run(w,path,writer,checkpoint_ticks=1,max_frames=40,paused=True,observer_class=Inspector)
    assert calls==[1,1] and instances[0].retried and instances[0].paused
    assert w.state()==before and load_game(path).state()==before


def test_extinct_terrain_timeline_pending_action_reload_and_ui_stay_terminal(tmp_path):
    import pytest
    w=TerrainWorld();w.request('rupture',2,2)
    for a in list(w._living_agents.values()):w.kill(a,'controlled extinction fixture')
    before=w.state();path=tmp_path/'ended.g5.sqlite';save_game(w,path);loaded=load_game(path)
    loaded.step(100);assert loaded.state()==before and loaded.interventions[0].status=='queued'
    for power in ('rain','drought','rupture','rewild','wellspring'):
        with pytest.raises(ValueError):loaded.request(power,2,2)
    v=TerrainObserver(loaded,paused=False)
    try:
        v.watch_id=v.selected
        v.handle([pygame.event.Event(pygame.KEYDOWN,key=k) for k in (pygame.K_e,pygame.K_SPACE,pygame.K_PERIOD)])
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(2*v.tile+1,2*v.tile+1))])
        v.advance(1);v.draw()
        assert v.paused and v.watch_id==1 and loaded.state()==before
    finally:pygame.quit()
