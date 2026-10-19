"""Quiet, fresh-process late-window timing; run AFTER scientific campaigns stop."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

from gnome_fortress.engine import World
from gnome_fortress.storage import save
from research.phase2_controls import Config, capacity, load_experiment
from research.study import write_csv

ROOT=Path('research/phase2')


def one(folder,out):
    source=json.loads((folder/'summary.json').read_text())
    cfg=Config(**source['config'])
    assert cfg.memory=='enabled'
    with capacity(cfg.slots):
        w=load_experiment(folder/'final.sqlite',cfg)
        assert w.digest()==source['final_digest']
        # Disable observational overrides; time the unmodified original implementation.
        w.__class__=World
        start=w.tick
        wall=time.perf_counter(); cpu=time.process_time()
        w.step(200)
        elapsed=time.perf_counter()-wall; cpu=time.process_time()-cpu
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
        result=dict(seed=w.seed,slots=cfg.slots,start_tick=start,ticks=200,wall_seconds=elapsed,
                    cpu_seconds=cpu,cpu_percent_one_core=cpu/elapsed*100,ticks_per_second=200/elapsed,
                    peak_rss_mib_including_load=peak,initial_digest=source['final_digest'],
                    final_digest=w.digest(),living_after=len(w.living()),source=str(folder),
                    note='Bare original World, separate quiet fresh process; input checkpoint unmodified',
                    production_snapshot_seconds=None,production_snapshot_tick=None)
        if start==100000 and w.seed==1:
            save_start=time.perf_counter()
            save(w,out.parent/'snapshot-probe.sqlite')
            result['production_snapshot_seconds']=time.perf_counter()-save_start
            result['production_snapshot_tick']=w.tick
        out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(json.dumps(result),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',type=Path)
    parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.case:
        one(args.case,args.out)
        return
    assert len(list((ROOT/'data/endurance').glob('*/summary.json')))==3
    assert len(list((ROOT/'data/memory').glob('*/summary.json')))==40
    outdir=ROOT/'data/tail-benchmark'
    outdir.mkdir(parents=True,exist_ok=True)
    cases=[ROOT/f'data/scaling/seed-11-slots-{slots}' for slots in (60,120,240,480,960)]
    cases+=[ROOT/f'data/endurance/seed-{seed:02d}' for seed in (1,2,3)]
    rows=[]
    for i,folder in enumerate(cases):
        target=outdir/f'case-{i}.json'
        subprocess.run([sys.executable,'-m','research.phase2_tailbench','--case',str(folder),'--out',str(target)],check=True)
        rows.append(json.loads(target.read_text()))
    write_csv(ROOT/'results/tail-benchmark.csv',rows)
    (ROOT/'tail-benchmark-manifest.json').write_text(json.dumps(dict(ticks=200,cases=[str(p) for p in cases],
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),quiet_sequential=True),indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
