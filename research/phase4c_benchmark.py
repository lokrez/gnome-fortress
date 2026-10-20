"""Small paired process-isolated observer overhead measurement, not a throughput campaign."""
import argparse
import json
import resource
import subprocess
import sys
import time

from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld
from research.phase4c_pilot import run_world


def worker(seed,condition,instrumented):
    start=time.perf_counter();cpu=time.process_time()
    if instrumented:
        metrics,world,_=run_world(seed,condition,300)
        auxiliary_json_bytes=len(json.dumps(metrics).encode())
    else:
        world=TelephoneWorld(seed,TelephoneConfig(condition));world.step(300);world.validate()
        auxiliary_json_bytes=0
    seconds=time.perf_counter()-start
    cpu_seconds=time.process_time()-cpu
    return dict(seed=seed,condition=condition,instrumented=instrumented,seconds=seconds,
        cpu_seconds=cpu_seconds,cpu_percent=cpu_seconds/seconds*100,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        auxiliary_json_bytes=auxiliary_json_bytes,digest=world.digest())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--condition',default='multihop');parser.add_argument('--instrumented',action='store_true')
    args=parser.parse_args()
    if args.worker:print(json.dumps(worker(args.seed,args.condition,args.instrumented)));return
    rows=[]
    for seed in (1,2,3):
        for measured in (False,True):
            cmd=[sys.executable,'-m','research.phase4c_benchmark','--worker','--seed',str(seed)]
            if measured:cmd.append('--instrumented')
            row=json.loads(subprocess.check_output(cmd,text=True));rows.append(row)
        assert rows[-1]['digest']==rows[-2]['digest']
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
