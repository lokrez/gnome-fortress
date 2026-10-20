"""Small isolated-process instrumentation; no endurance or optimization claims."""
import argparse
import gc
import json
import resource
import time
import tracemalloc

from gnome_fortress.engine import World
from research.phase4b_experiment import CONDITIONS, ThreeGnomesWorld


def measure(condition, repeats=64):
    tracemalloc.start()
    step_seconds=cpu_seconds=0.0
    max_python_peak=max_extra_bytes=0
    for seed in range(1,repeats+1):
        gc.collect();tracemalloc.reset_peak()
        world=ThreeGnomesWorld(seed,condition)
        start=time.perf_counter();cpu=time.process_time()
        world.step(3)
        cpu_seconds+=time.process_time()-cpu;step_seconds+=time.perf_counter()-start
        max_python_peak=max(max_python_peak,tracemalloc.get_traced_memory()[1])
        whole=json.dumps(world.state(),sort_keys=True,separators=(',',':'))
        base=json.dumps(World.state(world),sort_keys=True,separators=(',',':'))
        max_extra_bytes=max(max_extra_bytes,len(whole)-len(base))
        del whole,base,world
    tracemalloc.stop()
    return dict(condition=condition,repeats=repeats,ticks=repeats*3,scheduled_decisions=repeats*8,
                stepping_seconds=step_seconds,stepping_cpu_seconds=cpu_seconds,
                instrumented_ticks_per_second=repeats*3/step_seconds,
                peak_python_allocation_bytes=max_python_peak,
                peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                max_extra_serialized_state_bytes=max_extra_bytes,
                note='Tracemalloc enabled; step timing excludes construction/validation/serialization. Peak allocation includes construction; RSS includes imports/serialization.')


def bounded_storage():
    world=ThreeGnomesWorld(1);world.step(2)  # B/C still adjacent, C already informed
    proof=json.dumps(world.proofs[3],sort_keys=True)
    events=len(world.events)
    tracemalloc.start()
    for _ in range(500):world.contact(world.agents[2],world.agents[3])
    gc.collect();warm=tracemalloc.get_traced_memory()[0]
    for _ in range(10000):world.contact(world.agents[2],world.agents[3])
    gc.collect();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert world.rejections['duplicate_root']==10500
    assert world.messages==2 and len(world.audit)==128
    assert proof==json.dumps(world.proofs[3],sort_keys=True) and len(world.events)==events
    return dict(warmup_attempts=500,additional_attempts=10000,contact_distance=1,
                rejection_counts=dict(world.rejections),python_current_after_warmup=warm,
                python_current_after_stress=current,retained_growth_bytes=current-warm,
                peak_traced_bytes=peak,audit_entries=len(world.audit),message_count=world.messages,
                c_value=world.agents[3].learned['move:hazard'],
                proof_receipts=len(world.proofs[3]['move:hazard']['receipts']),
                core_events_unchanged=True,proof_unchanged=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--condition',choices=CONDITIONS)
    group.add_argument('--stress',action='store_true')
    args=parser.parse_args()
    print(json.dumps(bounded_storage() if args.stress else measure(args.condition),indent=2))
