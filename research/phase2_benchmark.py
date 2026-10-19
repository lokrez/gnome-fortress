"""Sequential, fresh-process scaling runs and fixed scheduler-only workloads."""
import argparse
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import resource
import subprocess
import sys
import time

from gnome_fortress.engine import World
from research.phase2_controls import CAPACITIES, Config, capacity, load_experiment

ROOT=Path('research/phase2')


def synthetic(slots,n,path):
    with capacity(slots):
        w=World(11)
        for _ in range(n-60):
            w._spawn(1,1,w.agents[1].traits,(1,2))
        for a in w.agents.values():
            if a.id%10==0:
                w.kill(a,'synthetic')
            elif a.id%4==0:
                a.sleep_until=1000000
        eligible=sum(a.alive and a.sleep_until<=w.tick for a in w.agents.values())
        count=10000
        blocks=[]
        start=time.perf_counter(); cpu=time.process_time()
        for _ in range(5):
            t=time.perf_counter()
            for _ in range(count//5):
                chosen=w.schedule()
                assert len(chosen)==min(eligible,slots)
            blocks.append((time.perf_counter()-t)/(count//5))
        wall=time.perf_counter()-start
        result=dict(slots=slots,total_identities=n,eligible=eligible,calls=count,
                    wall_seconds=wall,cpu_seconds=time.process_time()-cpu,
                    microseconds_per_call=wall/count*1e6,block_microseconds=[s*1e6 for s in blocks],
                    peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    note='Fixed synthetic alive/sleep/dead population; selection only, no biology/decisions')
        path.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--synthetic',type=int,nargs=2,metavar=('SLOTS','POPULATION'))
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.synthetic:
        synthetic(*args.synthetic,args.out)
        return
    data=ROOT/'data/scaling'
    specs=ROOT/'specs/scaling'
    specs.mkdir(parents=True,exist_ok=True)
    # Interleave capacities with seed, deterministically, to reduce drift/order bias.
    orders=[(60,240,960,120,480),(480,120,960,240,60),(120,480,60,960,240)]
    jobs=[]
    for seed,order in zip((11,12,13),orders):
        for slots in order:
            spec=dict(seed=seed,slots=slots,memory='enabled',ticks=3000,sample=100,
                      replay=seed==11,out=str(data/f'seed-{seed}-slots-{slots}'))
            path=specs/f'seed-{seed}-slots-{slots}.json'
            path.write_text(json.dumps(spec,indent=2,sort_keys=True)+'\n')
            jobs.append(path)
    manifest=dict(seeds=[11,12,13],ticks=3000,capacity_order=orders,run_order=[str(p) for p in jobs],
                  source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  code_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('research').glob('phase2_*.py'))})
    (ROOT/'scaling-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    for path in jobs:
        print(f'LAUNCH {path}',flush=True)
        subprocess.run([sys.executable,'-m','research.phase2_run','--spec',str(path)],check=True)
    synthetic_dir=ROOT/'data/synthetic'
    synthetic_dir.mkdir(parents=True,exist_ok=True)
    for n in (960,3840):
        for slots in CAPACITIES:
            subprocess.run([sys.executable,'-m','research.phase2_benchmark','--synthetic',str(slots),str(n),
                            '--out',str(synthetic_dir/f'n-{n}-slots-{slots}.json')],check=True)
    # Profiling is a separate job, never mixed into primary throughput numbers.
    with capacity(960):
        w=load_experiment(data/'seed-11-slots-960/final.sqlite',Config(960))
        profile=cProfile.Profile()
        profile.enable(); w.step(200); profile.disable()
        with (ROOT/'capacity-960-profile.txt').open('w') as f:
            pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(25)
    print('SCALING COMPLETE',flush=True)


if __name__=='__main__':
    main()
