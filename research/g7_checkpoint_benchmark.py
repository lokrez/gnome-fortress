"""Bounded save-pause comparison on generated state; never touches player saves."""
import argparse
import json
from pathlib import Path
import tempfile
import time

from gnome_fortress.runtime import CheckpointWorker
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game


def sample(worker_class,world,path):
    save_game(world,path);initial=world.state();tick=world.tick
    worker=worker_class(save_game);locks=getattr(worker,'locks_world',True)
    started=time.perf_counter();worker.start(world,path);capture=time.perf_counter()-started
    last=started;accumulator=0;gaps=[];frames=0
    try:
        while not worker.future.done():
            now=time.perf_counter();gap=now-last;last=now;gaps.append(gap);frames+=1
            if not locks:
                accumulator+=min(gap,.25)*15
                while accumulator>=1:world.step();accumulator-=1
            time.sleep(1/60)
        metrics=worker.poll();elapsed=time.perf_counter()-started
    finally:worker.close()
    assert load_game(path).state()==initial
    expected=TerrainWorld.from_state(initial);expected.step(world.tick-tick)
    assert expected.state()==world.state()
    return dict(worker=worker_class.__name__,saved_tick=metrics['tick'],live_tick=world.tick,
        live_ticks_during_save=world.tick-tick,capture_or_start_seconds=capture,
        total_save_wall_seconds=elapsed,writer_seconds=metrics['seconds'],service_iterations=frames,
        max_service_gap_seconds=max(gaps,default=0),snapshot_exact=True,live_continuation_exact=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ticks',type=int,default=3000)
    args=p.parse_args();world=TerrainWorld(1);world.step(args.ticks);initial=world.state()
    with tempfile.TemporaryDirectory() as folder:
        before=sample(CheckpointWorker,TerrainWorld.from_state(initial),Path(folder)/'before.g5.sqlite')
        after=sample(TerrainCheckpointWorker,TerrainWorld.from_state(initial),Path(folder)/'after.g5.sqlite')
    print(json.dumps(dict(seed=1,fixture_ticks=args.ticks,before=before,after=after,
        caveat='Single engineering measurement, generated fixture, no claim about laptop FPS or zero capture latency'),indent=2))


if __name__=='__main__':main()
