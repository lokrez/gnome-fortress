"""Post-optimization profiles, separate from accepted benchmark loop timings."""
import cProfile,json,pstats,time
from pathlib import Path
from gnome_fortress.storage import load,save
ROOT=Path('research/phase3')


def main():
    w=load('research/phase2/data/endurance/seed-01/final.sqlite');w.step(100)
    profile=cProfile.Profile();profile.enable();w.step(100);profile.disable()
    with (ROOT/'optimized-engine-profile.txt').open('w') as f:
        pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(30)
    target=ROOT/'data/profile-optimized.sqlite';first=save(w,target);w.step(30)
    profile=cProfile.Profile();profile.enable();metrics=save(w,target);profile.disable()
    with (ROOT/'optimized-save-profile.txt').open('w') as f:
        pstats.Stats(profile,stream=f).strip_dirs().sort_stats('cumulative').print_stats(35)
    (ROOT/'optimized-profile-metrics.json').write_text(json.dumps(dict(first=first,profiled_repeat=metrics),indent=2)+'\n')
    print('POST-OPTIMIZATION PROFILES COMPLETE',flush=True)

if __name__=='__main__':main()
