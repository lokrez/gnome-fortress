"""Matched no-save/full-snapshot/chronicle runs with explicit five-power inputs."""
import argparse,json,pickle,sqlite3,tempfile
from pathlib import Path
from types import SimpleNamespace
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker,capture_snapshot
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import load_game
from research.saveguard_replay import apply_inputs,SNAPSHOTS


class FullWorker(TerrainCheckpointWorker):
    def __init__(self):
        super().__init__();self.chronicle=SimpleNamespace(detach=capture_snapshot,invalidate=lambda:None)
    def prepare(self,w,budget=.004):pass


def compare(folder,seed):
    worlds=[TerrainWorld(seed) for _ in range(3)];workers=[FullWorker(),TerrainCheckpointWorker()]
    paths=[folder/'full.g5.sqlite',folder/'chronicle.g5.sqlite'];rows=[];restart=None
    rock=next((x,y) for y in range(worlds[0].height) for x in range(worlds[0].width) if worlds[0].cell(x,y).terrain=='rock')
    try:
        for tick in range(2401):
            for w in worlds:apply_inputs(w,rock)
            workers[1].prepare(worlds[2])
            if tick in SNAPSHOTS:
                expected=worlds[0].state()
                assert all(w.state()==expected for w in worlds)
                for worker,w,path in zip(workers,worlds[1:],paths):worker.start(w,path)
                for w in worlds:w.step()
                payloads=[]
                for worker,path in zip(workers,paths):
                    worker.future.result(timeout=30);metrics=worker.poll();saved=load_game(path)
                    assert saved.state()==expected and metrics['tick']==tick
                    with sqlite3.connect(path) as db:payloads.append(db.execute('SELECT payload,sha256 FROM game_checkpoint').fetchone())
                assert payloads[0]==payloads[1]
                if tick==20:restart=load_game(paths[1])
                rows.append(dict(snapshot=tick,live_tick=worlds[2].tick,exact=True,checksum=payloads[0][1]))
            else:
                for w in worlds:w.step()
        while restart.tick<worlds[0].tick:
            if restart.tick>20:apply_inputs(restart,rock)
            restart.step()
        assert restart.state()==worlds[0].state()==worlds[1].state()==worlds[2].state()
        return dict(seed=seed,snapshots=rows,digests=[w.digest() for w in worlds],reload_exact=True,summary=worlds[0].summary())
    finally:
        for worker in workers:worker.close()


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('docs/g8a2/evidence/replay.json'));args=p.parse_args();rows=[]
    with tempfile.TemporaryDirectory(prefix='g8a2-replay-') as root:
        for seed in (1,2):
            folder=Path(root)/str(seed);folder.mkdir();rows.append(compare(folder,seed));args.out.write_text(json.dumps(rows,indent=2)+'\n');print('verified',seed,flush=True)


if __name__=='__main__':main()
