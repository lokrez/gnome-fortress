"""Isolated generated-world save profiling; never opens a player's checkpoint."""
import argparse
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import pickle
import resource
import sqlite3
import subprocess
import sys
import tempfile
import time

from gnome_fortress.terrain_game import TerrainWorld, FORMAT
from gnome_fortress.terrain_storage import save_game, load_game, _read
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.runtime import CheckpointWorker


def profiled_save(world,path):
    """Phase instrument the existing strict update algorithm on isolated files."""
    phases={};wall=time.perf_counter();cpu=time.process_time()
    def measure(name,call):
        start=time.perf_counter();result=call();phases[name]=time.perf_counter()-start;return result
    measure('snapshot_validation',world.validate)
    measure('previous_checkpoint_validation',lambda:load_game(path))
    state=measure('canonical_state_assembly',world.state)
    payload=measure('json_serialization',lambda:json.dumps(state,sort_keys=True,separators=(',',':')))
    checksum=measure('checksum',lambda:hashlib.sha256(payload.encode()).hexdigest())
    with closing(measure('sqlite_connect',lambda:sqlite3.connect(path))) as db:
        db.execute('PRAGMA synchronous=FULL')
        measure('sqlite_begin',lambda:db.execute('BEGIN IMMEDIATE'))
        try:
            old=measure('transactional_previous_validation',lambda:_read(db))
            if world.tick<old.tick:raise ValueError('Checkpoint tick cannot move backward')
            measure('sqlite_payload_write',lambda:db.execute('UPDATE game_checkpoint SET format=?,payload=?,sha256=? WHERE id=1',(FORMAT,payload,checksum)))
            measure('sqlite_commit_fsync',db.commit)
        except BaseException:db.rollback();raise
    return dict(tick=world.tick,seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,
        phases_seconds=phases,file_bytes=Path(path).stat().st_size,writer_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def percentile(values,p):
    ordered=sorted(values);return ordered[min(len(ordered)-1,int((len(ordered)-1)*p))]


def sample(fixture,mode,folder,repeats,capture_method):
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    from gnome_fortress.terrain_viewer import TerrainObserver
    import pygame
    with open(fixture,'rb') as f:world=pickle.load(f) # trusted generated IPC, not a checkpoint
    if capture_method=='reference':
        import gnome_fortress.terrain_checkpoint as checkpoints
        checkpoints.capture_snapshot=lambda w:pickle.dumps(w,protocol=5)
    initial_state=world.state()
    initial_tick=world.tick;events=len(world.events);agents=len(world.agents);living=len(world.living())
    path=Path(folder)/(mode+'.g5.sqlite');save_game(world,path)
    observer=TerrainObserver(world,rate=15);observer.draw()
    worker=None if mode=='sync' else (CheckpointWorker if mode=='thread' else TerrainCheckpointWorker)(profiled_save)
    gaps=[];captures=[];metrics=[];notification=[];windows=[];ticks=0;wall=time.perf_counter();cpu=time.process_time()
    try:
        for _ in range(repeats):
            # Identical starting state for EVERY repetition, independent of the
            # previous save's wall time. Setup and correctness checks aren't frames.
            world=TerrainWorld.from_state(initial_state);observer=TerrainObserver(world,rate=15);observer.draw()
            expected=world.state();rng=world.rng.getstate();last=time.perf_counter();window_start=last
            if mode=='sync':
                start=time.perf_counter();m=profiled_save(world,path);captures.append(time.perf_counter()-start)
                observer.draw();gaps.append(time.perf_counter()-last)
            else:
                start=time.perf_counter();worker.start(world,path);captures.append(time.perf_counter()-start)
                accumulator=0
                while True:
                    now=time.perf_counter();gap=now-last;last=now;gaps.append(gap)
                    pygame.event.pump()
                    if not getattr(worker,'locks_world',True):
                        accumulator+=min(gap,.25)*15
                        while accumulator>=1:world.step();ticks+=1;accumulator-=1
                    observer.draw()
                    if worker.future.done():
                        ready=time.perf_counter();m=worker.poll();notification.append(time.perf_counter()-ready);break
                    time.sleep(1/60)
            windows.append(time.perf_counter()-window_start)
            metrics.append(m)
            saved=load_game(path)
            assert saved.state()==expected and saved.rng.getstate()==rng
            saved.step(world.tick-saved.tick)
            assert saved.state()==world.state() and saved.rng.getstate()==world.rng.getstate()
        elapsed=time.perf_counter()-wall
        return dict(mode=mode,capture_method=capture_method,active_save_window_seconds=sum(windows),
            active_window_simulation_ticks_per_second=ticks/sum(windows),fixture_tick=initial_tick,retained_agents=agents,living=living,events=events,
            sample_count=repeats,frame_samples=len(gaps),max_frame_gap_seconds=max(gaps),p95_frame_gap_seconds=percentile(gaps,.95),
            p99_frame_gap_seconds=percentile(gaps,.99),main_thread_capture_seconds=captures,save_metrics=metrics,
            simulation_ticks_during_saves=ticks,wall_seconds=elapsed,simulation_ticks_per_second=ticks/elapsed,
            main_cpu_seconds=time.process_time()-cpu,main_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            completion_notification_seconds=notification,file_bytes=path.stat().st_size,
            exact_snapshot_and_continuation=True,wait_for_tick_seconds=0,
            configured_game_interval_ticks=300,configured_simulation_rate=15,
            note='SDL-dummy actual renderer; bounded save windows, not overall gameplay FPS; no wall-clock inputs')
    finally:
        if worker:worker.close()
        pygame.quit()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path);p.add_argument('--modes',nargs='+',default=['sync','thread','spawn'])
    p.add_argument('--ticks',nargs='+',type=int,default=[0,1000,3000,10000]);p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--sample',type=Path);p.add_argument('--mode');p.add_argument('--folder',type=Path)
    p.add_argument('--capture-method',choices=['reference','containers'],default='containers')
    args=p.parse_args()
    if args.sample:
        result=sample(args.sample,args.mode,args.folder,args.repeats,args.capture_method)
        print('SAVEGUARD_JSON='+json.dumps(result));return
    results=[];world=TerrainWorld(1)
    with tempfile.TemporaryDirectory(prefix='gnome-saveguard-profile-') as root:
        root=Path(root)
        for tick in args.ticks:
            world.step(tick-world.tick);fixture=root/'generated.pickle';fixture.write_bytes(pickle.dumps(world,protocol=5))
            for mode in args.modes:
                folder=root/f'{tick}-{mode}';folder.mkdir()
                result=subprocess.run([sys.executable,'-m','research.saveguard_profile','--sample',str(fixture),'--mode',mode,
                    '--folder',str(folder),'--repeats',str(args.repeats),'--capture-method',args.capture_method],text=True,capture_output=True,check=True)
                line=next(s for s in result.stdout.splitlines() if s.startswith('SAVEGUARD_JSON='))
                results.append(json.loads(line.split('=',1)[1]));print(f'profile tick={tick} mode={mode} done',flush=True)
                if args.out:args.out.write_text(json.dumps(dict(seed=1,results=results),indent=2)+'\n')
    if not args.out:print(json.dumps(dict(seed=1,results=results),indent=2))


if __name__=='__main__':main()
