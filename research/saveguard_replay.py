"""Predeclared five-power, tick-boundary save/no-save equivalence experiment."""
import hashlib
import json
from pathlib import Path
import tempfile

from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import save_game,load_game

SNAPSHOTS=(0,9,10,19,20,21,29,30,31,60,1200,2400)


def apply_inputs(world,rock):
    schedule={0:[('rain',5,5,2,40),('rupture',5,5,None,None)],
              9:[('drought',5,5,2,30)],20:[('rewild',5,5,None,None)],
              29:[('wellspring',*rock,None,None)]}
    for kind,x,y,radius,duration in schedule.get(world.tick,[]):world.request(kind,x,y,radius,duration)


def run_comparison(folder):
    folder=Path(folder);worlds=[TerrainWorld(1) for _ in range(3)]
    rock=next((x,y) for y,row in enumerate(worlds[0].cells) for x,c in enumerate(row) if c.terrain=='rock')
    sync=folder/'sync.g5.sqlite';asyn=folder/'async.g5.sqlite';worker=TerrainCheckpointWorker()
    reload_world=None;records=[]
    try:
        for tick in range(2401):
            for w in worlds:apply_inputs(w,rock)
            if tick in SNAPSHOTS:
                expected=worlds[0].state();rng=worlds[0].rng.getstate()
                assert all(w.state()==expected and w.rng.getstate()==rng for w in worlds)
                save_game(worlds[1],sync);worker.start(worlds[2],asyn)
                # The detached copy is not allowed to observe this next tick.
                for w in worlds:w.step()
                worker.future.result(timeout=20);m=worker.poll();assert m['tick']==tick
                saved=load_game(asyn)
                assert saved.state()==load_game(sync).state()==expected and saved.rng.getstate()==rng
                records.append(dict(snapshot_tick=tick,live_tick=worlds[2].tick,
                    digest=saved.digest(),state_and_rng_exact=True,reported_tick=m['tick']))
                if tick==20:reload_world=saved
            else:
                for w in worlds:w.step()
        assert worlds[0].state()==worlds[1].state()==worlds[2].state()
        assert len(worlds[0].agents)>60 and any(e.kind=='death' for e in worlds[0].events)
        # Reload during active Rain/Drought and queued Rewild; replay only future
        # commands. Tick-20 inputs are already in the saved snapshot.
        while reload_world.tick<worlds[0].tick:
            if reload_world.tick>20:apply_inputs(reload_world,rock)
            reload_world.step()
        assert reload_world.state()==worlds[0].state() and reload_world.rng.getstate()==worlds[0].rng.getstate()
        return dict(seed=1,final_tick=worlds[0].tick,wellspring_target=rock,
            input_schedule={'0':['rain(5,5,r2,d40)','rupture(5,5,r2)'],'9':['drought(5,5,r2,d30)'],
                            '20':['rewild(5,5,r2)'],'29':[f'wellspring{rock}']},
            snapshots=records,final_digests=dict(zip(('no_save','synchronous','asynchronous'),[w.digest() for w in worlds])),
            rng_sha256=hashlib.sha256(json.dumps(worlds[0].rng.getstate()).encode()).hexdigest(),
            reload_tick=20,reload_continuation_exact=True,summary=worlds[0].summary(),
            births_after_founders=len(worlds[0].agents)-60,
            deaths=sum(not a.alive for a in worlds[0].agents.values()))
    finally:worker.close()


def main():
    with tempfile.TemporaryDirectory(prefix='saveguard-replay-') as folder:print(json.dumps(run_comparison(folder),indent=2))


if __name__=='__main__':main()
