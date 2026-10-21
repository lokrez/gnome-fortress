"""Bounded generated-world capture diagnosis. Never reads a player checkpoint."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
import multiprocessing
from pathlib import Path
import pickle
import resource
import tempfile
import time
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_checkpoint import capture_snapshot,_Snapshot


def decode_probe(blob):
    start=time.perf_counter();w=pickle.loads(blob)
    return dict(seconds=time.perf_counter()-start,tick=w.tick,rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def echo_probe(blob):return len(blob)


def phases(w):
    timings={};start=time.perf_counter()
    def timed(name,fn):
        t=time.perf_counter();value=fn();timings[name]=(time.perf_counter()-t)*1000;return value
    graph=vars(w).copy();graph.pop('_living_agents')
    graph['rng']=timed('rng_and_scheduler',lambda:w.rng.getstate())
    graph['cells']=timed('terrain',lambda:[[vars(c) for c in row] for row in w.cells])
    agents=timed('agent_headers',lambda:{i:vars(a).copy() for i,a in w.agents.items()})
    memories=timed('episodes',lambda:{i:[vars(m) for m in a.memories] for i,a in w.agents.items()})
    for i in agents:agents[i]['memories']=memories[i]
    # Header dictionaries retain nested references until pickle completes, exactly as reference capture.
    graph['agents']=agents
    graph['events']=timed('events',lambda:[vars(e) for e in w.events])
    graph['interventions']=timed('interventions',lambda:[vars(p) for p in w.interventions])
    blob=timed('pickle',lambda:pickle.dumps(_Snapshot(graph),protocol=5))
    timings['total']=(time.perf_counter()-start)*1000
    return timings,blob


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('docs/g8a2/evidence/before.json'))
    p.add_argument('--fixtures',type=Path,required=True);p.add_argument('--ticks',nargs='+',type=int,default=[3000,10000,26000]);args=p.parse_args()
    args.fixtures.mkdir(parents=True,exist_ok=True);w=TerrainWorld(1);rows=[]
    with ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn')) as pool:
        for tick in args.ticks:
            start=time.perf_counter();w.step(tick-w.tick);generation=time.perf_counter()-start
            sample=[]
            for _ in range(3):t,blob=phases(w);sample.append(t)
            decoded=pool.submit(decode_probe,blob).result()
            start=time.perf_counter();assert pool.submit(echo_probe,blob).result()==len(blob);transfer=time.perf_counter()-start
            fixture=args.fixtures/f'{tick}.pickle';fixture.write_bytes(blob)
            row=dict(tick=tick,living=len(w.living()),retained=len(w.agents),events=len(w.events),generation_seconds=generation,
                samples_ms=sample,snapshot_bytes=len(blob),transfer_seconds=transfer,decode=decoded,
                rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,fixture=str(fixture))
            rows.append(row);args.out.write_text(json.dumps(dict(seed=1,rows=rows),indent=2)+'\n');print('profiled',tick,flush=True)


if __name__=='__main__':main()
