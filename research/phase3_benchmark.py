"""Sequential fresh-process comparisons against the byte-frozen Phase 2 oracle."""
import argparse,cProfile,csv,hashlib,json,os,platform,pstats,resource,subprocess,sys,time
from pathlib import Path

from research.phase3_check import fingerprint,assert_exact

ROOT=Path('research/phase3')


def dump(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def case(spec):
    if spec['variant']=='reference':
        from research.phase3.reference.engine import World
        from research.phase3.reference.storage import load,save
    else:
        from gnome_fortress.engine import World
        from gnome_fortress.storage import load,save
    out=ROOT/'data'/spec['name']/spec['variant'];out.mkdir(parents=True,exist_ok=False)
    t=time.perf_counter();w=load(spec['source']) if spec.get('source') else World(11)
    result=dict(spec,load_seconds=time.perf_counter()-t,load_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,initial_digest=fingerprint(w),start_tick=w.tick)
    cpu=time.process_time();t=time.perf_counter();w.step(spec['ticks']);elapsed=time.perf_counter()-t
    result.update(loop_seconds=elapsed,ticks_per_second=spec['ticks']/elapsed,
                  cpu_seconds=time.process_time()-cpu,cpu_percent_one_core=(time.process_time()-cpu)/elapsed*100,
                  simulation_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  after_loop_digest=fingerprint(w))
    target=out/'checkpoint.sqlite'
    t=time.perf_counter();metrics=save(w,target)
    result.update(first_save_seconds=time.perf_counter()-t,first_save_metrics=metrics,file_bytes=target.stat().st_size)
    w.step(30)
    t=time.perf_counter();metrics=save(w,target)
    result.update(repeated_save_seconds=time.perf_counter()-t,repeated_save_metrics=metrics,
                  repeated_file_bytes=target.stat().st_size,final_digest=fingerprint(w))
    t=time.perf_counter();restored=load(target)
    result['reload_seconds']=time.perf_counter()-t
    assert_exact(w,restored)
    w.step(20);restored.step(20)
    assert_exact(w,restored)
    result.update(continuation_digest=fingerprint(w),exact_reload_continuation=True,
                  identities=len(w.agents),living=len(w.living()),events=len(w.events),
                  overall_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
    dump(out/'result.json',result)
    print('COMPLETE',spec['name'],spec['variant'],round(result['ticks_per_second'],1),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=Path);args=parser.parse_args()
    if args.case:case(json.loads(args.case.read_text()));return
    specs=ROOT/'specs';specs.mkdir(exist_ok=True)
    cases=[dict(name='young',ticks=3000),dict(name='tick-20000-seed-1',ticks=200,
        source='research/phase1/data/seed-01/final.sqlite')]
    cases += [dict(name=f'tick-100000-seed-{seed}',ticks=200,
        source=f'research/phase2/data/endurance/seed-{seed:02d}/final.sqlite') for seed in (1,2,3)]
    manifest=dict(reference_commit='5efc9b1bfdd8d49a13aefd4e9256e6c1e87c024f',
        code_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            sorted(list(Path('gnome_fortress').glob('*.py'))+list(Path('research').glob('phase3_*.py')))},
        python=sys.version,platform=platform.platform(),logical_cpus=os.cpu_count(),cases=cases)
    dump(ROOT/'benchmark-manifest.json',manifest)
    rows=[]
    for i,c in enumerate(cases):
        variants=('reference','optimized') if i%2==0 else ('optimized','reference')
        pair=[]
        for variant in variants:
            spec=dict(c,variant=variant);path=specs/f"{c['name']}-{variant}.json";dump(path,spec)
            subprocess.run([sys.executable,'-m','research.phase3_benchmark','--case',str(path)],check=True)
            row=json.loads((ROOT/'data'/c['name']/variant/'result.json').read_text());rows.append(row);pair.append(row)
        for field in ('initial_digest','after_loop_digest','final_digest','continuation_digest'):
            assert pair[0][field]==pair[1][field],(c['name'],field)
    dump(ROOT/'benchmark-results.json',rows)
    fields=['name','variant','start_tick','ticks','ticks_per_second','loop_seconds','cpu_percent_one_core',
            'load_peak_rss_mib','simulation_peak_rss_mib','overall_peak_rss_mib','first_save_seconds','repeated_save_seconds',
            'file_bytes','repeated_file_bytes','load_seconds','reload_seconds','identities','events','final_digest']
    with (ROOT/'benchmarks.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    print('ALL FIVE MATCHED CASES EXACT',flush=True)

if __name__=='__main__':main()
