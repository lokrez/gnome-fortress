"""Launch only pre-registered A/C jobs, with independent fresh worker processes."""
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import hashlib
import json
import multiprocessing
from pathlib import Path
import subprocess

from research.phase2_run import run

ROOT=Path('research/phase2')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args()
    assert len(list((ROOT/'data/scaling').glob('*/summary.json')))==15, 'Finish uncontended scaling first'
    assert len(list((ROOT/'data/synthetic').glob('*.json')))==10, 'Finish scheduler-only benchmark first'
    assert (ROOT/'capacity-960-profile.txt').exists()
    # No baseline or historical artifact edits are permitted.
    subprocess.run(['git','diff','--exit-code','f32c1a6','--','gnome_fortress','tests','pyproject.toml','requirements-tested.txt'],check=True)
    subprocess.run(['git','diff','--exit-code','232dd30','--','research/phase1','research/study.py','research/verify.py','research/analyze.py','research/test_study.py','research/test_analysis.py'],check=True)
    jobs=[]
    for seed in (1,2,3):
        jobs.append(dict(seed=seed,slots=60,memory='enabled',ticks=100000,sample=100,
                         resume=f'research/phase1/data/seed-{seed:02d}/final.sqlite',
                         checkpoints=[50000],final_checkpoint_check=True,
                         out=str(ROOT/f'data/endurance/seed-{seed:02d}')))
    for seed in range(1001,1021):
        for memory in ('enabled','ablated'):
            jobs.append(dict(seed=seed,slots=60,memory=memory,ticks=20000,sample=100,
                             replay=seed==1001,out=str(ROOT/f'data/memory/seed-{seed}-{memory}')))
    code_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('research').glob('phase2_*.py'))}
    specs=ROOT/'specs/science'
    specs.mkdir(parents=True,exist_ok=True)
    for spec in jobs:
        name=Path(spec['out']).name
        if 'endurance' in spec['out']:
            name='endurance-'+name
        (specs/f'{name}.json').write_text(json.dumps(spec,indent=2,sort_keys=True)+'\n')
    manifest=dict(parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  original_rule_commit='f32c1a6',phase1_commit='232dd30',workers=args.workers,
                  code_hashes=code_hashes,protocol_sha256=hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),
                  jobs=jobs,notes='A/C are observationally instrumented; only A ablated readout changes policy. Capacities remain 60. Fresh spawned process per job.')
    (ROOT/'science-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    context=multiprocessing.get_context('spawn')
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=context,max_tasks_per_child=1) as pool:
        future_to_job={pool.submit(run,spec):spec for spec in jobs}
        for future in as_completed(future_to_job):
            spec=future_to_job[future]
            result=future.result()
            print(f"VERIFIED {spec['out']}: {result['final_digest']}",flush=True)
    print('SCIENCE COMPLETE',flush=True)


if __name__=='__main__':
    main()
