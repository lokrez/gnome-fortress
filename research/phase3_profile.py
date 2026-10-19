"""Profile the pinned implementation before changing production code."""
import cProfile,json,pstats,time,resource
from pathlib import Path
from research.phase3.reference.storage import load,save

ROOT=Path('research/phase3')

def main():
    source=Path('research/phase2/data/endurance/seed-01/final.sqlite')
    start=time.perf_counter(); w=load(source)
    result={'source':str(source),'tick':w.tick,'living':len(w.living()),'identities':len(w.agents),
            'events':len(w.events),'load_seconds':time.perf_counter()-start}
    start=time.perf_counter(); cpu=time.process_time(); w.step(100)
    elapsed=time.perf_counter()-start
    result['loop']={'ticks':100,'seconds':elapsed,'ticks_per_second':100/elapsed,'cpu_seconds':time.process_time()-cpu}
    prof=cProfile.Profile(); prof.enable(); w.step(100); prof.disable()
    with (ROOT/'reference-engine-profile.txt').open('w') as f:
        pstats.Stats(prof,stream=f).strip_dirs().sort_stats('cumulative').print_stats(30)
    prof=cProfile.Profile(); prof.enable(); save(w,ROOT/'data/profile-reference.sqlite'); prof.disable()
    with (ROOT/'reference-save-profile.txt').open('w') as f:
        pstats.Stats(prof,stream=f).strip_dirs().sort_stats('cumulative').print_stats(35)
    result['peak_rss_mib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    (ROOT/'profile-pilot.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__': main()
