import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import time
import pickle
import pygame
import pytest

from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker,capture_snapshot
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_viewer import TerrainObserver
from gnome_fortress.god_viewer import run


def delayed_save(world,path):
    time.sleep(.2)
    return save_game(world,path)


def failed_save(world,path):raise OSError('controlled isolated writer failure')


def test_snapshot_detaches_slots_and_all_later_world_changes():
    w=TerrainWorld();w.step(20);state=capture_snapshot(w);before=pickle.loads(state)
    w.slots[:]=[None]*60;w.request('rupture',2,2);w.step(10)
    assert pickle.loads(state).state()==before.state()
    assert pickle.loads(state).slots is not w.slots


def test_spawned_save_exact_while_live_world_steps_and_casts(tmp_path):
    w=TerrainWorld();w.step(10);path=tmp_path/'async.g5.sqlite';save_game(w,path)
    expected=TerrainWorld.from_state(w.state());worker=TerrainCheckpointWorker(delayed_save)
    try:
        worker.start(w,path)
        assert not worker.locks_world
        with pytest.raises(RuntimeError):worker.start(w,path)
        w.request('rewild',2,2);w.step(30)
        metrics=worker.future.result(timeout=10);assert metrics['tick']==10
        assert worker.poll()==metrics and not worker.pending
        saved=load_game(path);assert saved.state()==expected.state()
        saved.step(20);expected.step(20);assert saved.state()==expected.state()
        assert w.tick==40
    finally:worker.close()


def test_isolated_failure_preserves_old_checkpoint_and_can_retry(tmp_path):
    w=TerrainWorld();path=tmp_path/'failure.g5.sqlite';save_game(w,path);raw=path.read_bytes()
    worker=TerrainCheckpointWorker(failed_save)
    try:
        w.step();worker.start(w,path)
        with pytest.raises(OSError):worker.future.result(timeout=10)
        with pytest.raises(OSError):worker.poll()
        assert not worker.pending and path.read_bytes()==raw
        worker.callback=save_game;worker.start(w,path);worker.future.result(timeout=10);worker.poll()
        assert load_game(path).state()==w.state()
    finally:worker.close()


def test_viewer_progresses_and_casts_during_isolated_save_exit_flushes_latest(tmp_path):
    instances=[];w=TerrainWorld();path=tmp_path/'viewer.g5.sqlite'
    class Inspector(TerrainObserver):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.save_requested=True;self.changed=False;instances.append(self)
        def handle(self,events):
            super().handle(events)
            if getattr(self,'checkpoint_pending',False) and not self.changed:
                assert not self.saving
                self.changed=True
                super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_r),
                    pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(50,70)),
                    pygame.event.Event(pygame.KEYDOWN,key=pygame.K_PERIOD)])
            elif 'Saved tick' in self.notice:self.running=False
    run(w,path,delayed_save,paused=True,max_frames=120,observer_class=Inspector,worker_class=TerrainCheckpointWorker)
    assert instances[0].changed and w.tick==1 and len(w.interventions)==1
    assert load_game(path).tick==0 and not load_game(path).interventions
    # Same final flush as god_world.main: wait for worker, then save latest live state.
    save_game(w,path);assert load_game(path).state()==w.state()


def crashed_save(world,path):os._exit(9)


def test_crashed_writer_keeps_commit_and_explicit_retry_uses_new_process(tmp_path):
    from concurrent.futures.process import BrokenProcessPool
    w=TerrainWorld();path=tmp_path/'crash.g5.sqlite';save_game(w,path);raw=path.read_bytes()
    worker=TerrainCheckpointWorker(crashed_save)
    try:
        w.step();worker.start(w,path)
        with pytest.raises(BrokenProcessPool):worker.future.result(timeout=10)
        with pytest.raises(BrokenProcessPool):worker.poll()
        assert path.read_bytes()==raw
        worker.callback=save_game;worker.start(w,path);worker.future.result(timeout=10);worker.poll()
        assert load_game(path).state()==w.state()
    finally:worker.close()
