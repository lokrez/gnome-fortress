"""P0: isolated process ownership, bounded writes, exact scientific replay."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

import pygame
import pytest

from gnome_fortress.game_session import game_session,checkpoint_write_lock,SaveInUse
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import save_game as save_legacy,load_game as load_legacy
from gnome_fortress.god_viewer import run
from gnome_fortress.terrain_viewer import TerrainObserver


def command(path,legacy=False):
    return [sys.executable,'-m','gnome_fortress.god_demo' if legacy else 'gnome_fortress.god_world','--db',str(path)]


def wait_for(test,seconds=8):
    end=time.monotonic()+seconds
    while not test():
        if time.monotonic()>end:pytest.fail('child did not reach expected boundary')
        time.sleep(.02)


@pytest.mark.parametrize('legacy',[False,True])
def test_guard_before_loading_canonical_alias_and_separate_save(tmp_path,legacy):
    path=tmp_path/('busy.g1.sqlite' if legacy else 'busy.g5.sqlite');path.write_bytes(b'deliberately invalid')
    alias=tmp_path/('alias.g1.sqlite' if legacy else 'alias.g5.sqlite');alias.symlink_to(path)
    with game_session(path):
        result=subprocess.run(command(alias,legacy)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=6)
        assert result.returncode==2 and 'already in use' in result.stderr
        assert path.read_bytes()==b'deliberately invalid'
        other=tmp_path/('other.g1.sqlite' if legacy else 'other.g5.sqlite')
        result=subprocess.run(command(other,legacy)+['--headless','--ticks','1'],capture_output=True,text=True,timeout=6)
        assert result.returncode==0,result.stderr
        assert (load_legacy if legacy else load_game)(other).tick==1


@pytest.mark.parametrize('legacy',[False,True])
def test_real_owner_stop_continue_kill_relaunch(tmp_path,legacy):
    path=tmp_path/('signal.g1.sqlite' if legacy else 'signal.g5.sqlite')
    (save_legacy if legacy else save_game)((GameWorld if legacy else TerrainWorld)(),path)
    process=subprocess.Popen(command(path,legacy)+['--paused'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        lock=Path(str(path)+'.lock');wait_for(lambda:lock.exists() and lock.read_text()==str(process.pid))
        process.send_signal(signal.SIGSTOP)
        # Wait for the actual stopped state, not merely signal delivery.
        wait_for(lambda:Path(f'/proc/{process.pid}/status').read_text().split('State:')[1].lstrip().startswith('T'))
        result=subprocess.run(command(path,legacy)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert result.returncode==2 and 'already in use' in result.stderr
        process.send_signal(signal.SIGCONT)
        wait_for(lambda:not Path(f'/proc/{process.pid}/status').read_text().split('State:')[1].lstrip().startswith('T'))
        process.kill();process.wait(timeout=5)
        result=subprocess.run(command(path,legacy)+['--headless','--ticks','1'],capture_output=True,text=True,timeout=6)
        assert result.returncode==0,result.stderr
        assert (load_legacy if legacy else load_game)(path).tick==1
    finally:
        if process.poll() is None:process.kill();process.wait()


@pytest.mark.parametrize('legacy',[False,True])
def test_stale_tick_rejected_same_tick_requests_allowed(tmp_path,legacy):
    path=tmp_path/('tick.g1.sqlite' if legacy else 'tick.g5.sqlite')
    world=(GameWorld if legacy else TerrainWorld)();write=save_legacy if legacy else save_game;read=load_legacy if legacy else load_game
    old=(GameWorld if legacy else TerrainWorld).from_state(world.state());world.step(2);write(world,path);raw=path.read_bytes()
    with pytest.raises(ValueError,match='backward'):write(old,path)
    assert path.read_bytes()==raw and read(path).tick==2
    world.request('rain',2,2);write(world,path);assert read(path).state()==world.state()


def test_writer_gate_refuses_session_before_loading(tmp_path):
    path=tmp_path/'busy.g5.sqlite';path.write_bytes(b'not loaded')
    with checkpoint_write_lock(path):
        result=subprocess.run(command(path)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert result.returncode==2 and 'writer is still active' in result.stderr
        assert path.read_bytes()==b'not loaded'


def descriptor_check_save(world,path):
    # Spawned child intentionally opens only writer.lock; owner fd is not inherited.
    for fd in Path('/proc/self/fd').iterdir():
        try:target=os.readlink(fd)
        except FileNotFoundError:continue
        assert target!=str(Path(str(path)+'.lock').resolve())
    return save_game(world,path)


def test_worker_does_not_inherit_owner_descriptor(tmp_path):
    path=tmp_path/'descriptors.g5.sqlite';world=TerrainWorld()
    with game_session(path):
        worker=TerrainCheckpointWorker(descriptor_check_save)
        try:
            worker.start(world,path);worker.future.result(timeout=10);assert worker.poll()['tick']==0
        finally:worker.close()
    with game_session(path):assert load_game(path).state()==world.state()


def orphan_gate_save(world,path):
    path=Path(path);Path(str(path)+'.ready').touch()
    wait_until=time.monotonic()+12
    while not Path(str(path)+'.release').exists():
        if time.monotonic()>wait_until:raise TimeoutError('harness release missing')
        time.sleep(.01)
    result=save_game(world,path)
    Path(str(path)+'.done').touch();return result


def test_killed_parent_active_writer_drains_before_relaunch(tmp_path):
    path=tmp_path/'orphan.g5.sqlite';save_game(TerrainWorld(),path)
    # Harness-owned parent and child only. Callback module is importable by spawn.
    script='''from pathlib import Path
import sys,time
from gnome_fortress.game_session import game_session
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import load_game
from test_saveguard import orphan_gate_save
if __name__=='__main__':
 p=Path(sys.argv[1])
 with game_session(p):
  w=load_game(p);w.step();worker=TerrainCheckpointWorker(orphan_gate_save);worker.start(w,p)
  time.sleep(30)
'''
    env={**os.environ,'PYTHONPATH':str(Path(__file__).parent)+os.pathsep+str(Path.cwd())}
    process=subprocess.Popen([sys.executable,'-c',script,str(path)],env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        wait_for(lambda:Path(str(path)+'.ready').exists())
        process.kill();process.wait(timeout=4)
        result=subprocess.run(command(path)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert result.returncode==2 and 'writer is still active' in result.stderr
        Path(str(path)+'.release').touch();wait_for(lambda:Path(str(path)+'.done').exists())
        # writer exits after callback; gate may precede marker by a few instructions
        wait_for(lambda:writer_available(path))
        result=subprocess.run(command(path)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=6)
        assert result.returncode==0,result.stderr
        assert load_game(path).tick==1
    finally:
        Path(str(path)+'.release').touch()
        if process.poll() is None:process.kill();process.wait()


def writer_available(path):
    try:
        with checkpoint_write_lock(path):return True
    except SaveInUse:return False


def test_queued_orphan_cannot_start_write(tmp_path):
    # Real spawned child has a real PPID. Incorrect/dead owner is rejected before
    # unpickling or invoking the callback, even when bytes are deliberately invalid.
    from concurrent.futures import ProcessPoolExecutor
    import multiprocessing
    from gnome_fortress.terrain_checkpoint import _save_snapshot
    path=tmp_path/'never.g5.sqlite'
    with ProcessPoolExecutor(1,mp_context=multiprocessing.get_context('spawn')) as pool:
        future=pool.submit(_save_snapshot,b'invalid',path,save_game,-1)
        with pytest.raises(RuntimeError,match='owner exited'):future.result(timeout=8)
    assert not path.exists()


from research.saveguard_replay import apply_inputs,run_comparison


def test_no_save_sync_async_exact_all_powers_births_deaths_and_reload(tmp_path):
    result=run_comparison(tmp_path)
    assert len(set(result['final_digests'].values()))==1
    assert result['reload_continuation_exact'] and result['reload_tick']==20
    assert result['births_after_founders']>0 and result['deaths']>0


def test_duplicate_manual_requests_coalesce_and_report_captured_tick(tmp_path,monkeypatch):
    import pickle
    from concurrent.futures import Future
    from gnome_fortress.terrain_checkpoint import capture_snapshot
    world=TerrainWorld();path=tmp_path/'queue.g5.sqlite';starts=[];instances=[]
    class Clock:
        def tick(self,hz):return 0
    class Worker:
        locks_world=False
        def __init__(self,callback):self.future=None;self.snapshot=None;instances.append(self)
        @property
        def pending(self):return self.future is not None
        def start(self,w,path):
            assert not self.pending
            starts.append(w.tick);self.snapshot=capture_snapshot(w);self.future=Future()
        def complete(self):
            self.future.set_result(save_game(pickle.loads(self.snapshot),path))
        def poll(self):
            future,self.future=self.future,None;return future.result()
        def close(self):assert self.future is None
    class Observer(TerrainObserver):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.frame=0;self.notices=[]
        def handle(self,events):
            self.frame+=1
            events=[]
            if self.frame<=4:events=[pygame.event.Event(pygame.KEYDOWN,key=pygame.K_s)]*25
            super().handle(events)
            if self.frame in (6,9):instances[0].complete()
            if self.frame==10:
                assert self.notice==f'Saved tick {starts[-1]}'
                assert self.world.tick>starts[-1];self.running=False
            else:self.world.step()
    monkeypatch.setattr(pygame.time,'Clock',Clock)
    run(world,path,save_game,checkpoint_ticks=1000,paused=True,max_frames=12,observer_class=Observer,worker_class=Worker)
    assert starts==[1,6] and load_game(path).tick==6 and world.tick==9


def test_failed_save_visible_after_resume_no_automatic_retry(tmp_path,monkeypatch):
    from concurrent.futures import Future
    instances=[];calls=[];w=TerrainWorld()
    class Clock:
        def tick(self,hz):return 100
    class Worker:
        locks_world=False
        def __init__(self,callback):self.future=None
        @property
        def pending(self):return self.future is not None
        def start(self,world,path):
            calls.append(world.tick);self.future=Future();self.future.set_exception(OSError('controlled full disk'))
        def poll(self):
            future,self.future=self.future,None;return future.result()
        def close(self):pass
    class Observer(TerrainObserver):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.frame=0;self.save_requested=True;instances.append(self)
        def handle(self,events):
            self.frame+=1
            super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)] if self.frame==3 else [])
            if self.frame==6:self.running=False
    monkeypatch.setattr(pygame.time,'Clock',Clock)
    run(w,tmp_path/'fail.g5.sqlite',save_game,checkpoint_ticks=1,max_frames=8,paused=True,observer_class=Observer,worker_class=Worker)
    assert calls==[0] and instances[0].save_error and not instances[0].paused and w.tick>0


def test_sigkill_open_transaction_retains_full_previous_world(tmp_path):
    w=TerrainWorld();apply_inputs(w,(1,0));w.step(3)
    path=tmp_path/'transaction.g5.sqlite';save_game(w,path)
    script='''import sqlite3,sys,time
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA synchronous=FULL');c.execute('BEGIN IMMEDIATE')
c.execute("UPDATE game_checkpoint SET payload='torn',sha256='wrong'")
print('transaction open',flush=True);time.sleep(30)
'''
    process=subprocess.Popen([sys.executable,'-c',script,str(path)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='transaction open'
        process.kill();process.wait(timeout=4)
        assert load_game(path).state()==w.state()
        with game_session(path):assert load_game(path).rng.getstate()==w.rng.getstate()
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_async_extinct_world_keeps_pending_actions_terminal(tmp_path):
    w=TerrainWorld();w.request('rupture',2,2)
    for a in list(w.living()):w.kill(a,'controlled extinction fixture')
    state=w.state();worker=TerrainCheckpointWorker();path=tmp_path/'extinct.g5.sqlite'
    try:
        worker.start(w,path);w.step(20);worker.future.result(timeout=10);assert worker.poll()['tick']==0
        loaded=load_game(path);loaded.step(20);assert loaded.state()==state
        with pytest.raises(ValueError):loaded.request('rewild',2,2)
    finally:worker.close()


def test_worker_rejects_research_path_before_creating_sidecars():
    from gnome_fortress.game_storage import RESEARCH
    path=RESEARCH/'saveguard-protection-test.g5.sqlite';worker=TerrainCheckpointWorker()
    try:
        worker.start(TerrainWorld(),path)
        with pytest.raises(ValueError):worker.future.result(timeout=2)
        with pytest.raises(ValueError):worker.poll()
        assert not path.exists() and not Path(str(path)+'.lock').exists() and not Path(str(path)+'.writer.lock').exists()
    finally:worker.close()


@pytest.mark.parametrize('legacy',[False,True])
def test_hot_journal_real_page_spill_kill_and_locked_recovery(tmp_path,legacy):
    from gnome_fortress.terrain_storage import recover_game
    from gnome_fortress.game_storage import recover_game as recover_legacy
    from gnome_fortress.storage import save as research_save
    from gnome_fortress.engine import World
    recover=recover_legacy if legacy else recover_game;read=load_legacy if legacy else load_game
    path=tmp_path/('hot.g1.sqlite' if legacy else 'hot.g5.sqlite')
    w=(GameWorld if legacy else TerrainWorld)();(save_legacy if legacy else save_game)(w,path)
    with pytest.raises(ValueError,match='ownership'):recover(path)
    script='''import sqlite3,sys,time
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA synchronous=FULL');c.execute('PRAGMA cache_size=3')
c.execute('BEGIN IMMEDIATE');c.execute('UPDATE game_checkpoint SET payload=?,sha256=?',('x'*2000000,'wrong'))
print('spilled',flush=True);time.sleep(30)
'''
    process=subprocess.Popen([sys.executable,'-c',script,str(path)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='spilled'
        process.kill();process.wait(timeout=4)
        assert Path(str(path)+'-journal').exists()
        # Original archive reader still refuses a write-needing recovery.
        import sqlite3
        with pytest.raises(sqlite3.OperationalError):read(path)
        # Actual launcher owns recovery and resumes the exact committed world.
        result=subprocess.run(command(path,legacy)+['--headless','--ticks','0'],capture_output=True,text=True,timeout=7)
        assert result.returncode==0,result.stderr
        assert read(path).state()==w.state() and read(path).rng.getstate()==w.rng.getstate()
        foreign=tmp_path/('foreign.g1.sqlite' if legacy else 'foreign.g5.sqlite');research_save(World(),foreign);raw=foreign.read_bytes()
        with game_session(foreign):
            with pytest.raises(ValueError,match='supported'):recover(foreign)
        assert foreign.read_bytes()==raw
    finally:
        if process.poll() is None:process.kill();process.wait()


def crashed_hot_save(world,path):
    import sqlite3
    db=sqlite3.connect(path);db.execute('PRAGMA synchronous=FULL');db.execute('PRAGMA cache_size=3')
    db.execute('BEGIN IMMEDIATE');db.execute('UPDATE game_checkpoint SET payload=?,sha256=?',('x'*2000000,'bad'))
    os._exit(9)


def test_hot_journal_writer_crash_retry_while_owner_remains_alive(tmp_path):
    from concurrent.futures.process import BrokenProcessPool
    import sqlite3
    w=TerrainWorld();path=tmp_path/'retry-hot.g5.sqlite';save_game(w,path)
    with game_session(path):
        worker=TerrainCheckpointWorker(crashed_hot_save)
        try:
            w.step();worker.start(w,path)
            with pytest.raises(BrokenProcessPool):worker.future.result(timeout=8)
            with pytest.raises(BrokenProcessPool):worker.poll()
            assert Path(str(path)+'-journal').exists()
            with pytest.raises(sqlite3.OperationalError):load_game(path)
            worker.callback=save_game;worker.start(w,path);worker.future.result(timeout=8)
            assert worker.poll()['tick']==1 and load_game(path).state()==w.state()
        finally:worker.close()
