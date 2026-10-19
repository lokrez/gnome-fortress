"""Actual Pygame dummy-driver loop measurements; not desktop/GPU frame rates."""
import argparse,hashlib,json,os,resource,subprocess,sys,threading,time
from pathlib import Path
os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
from research.phase3_check import fingerprint
ROOT=Path('research/phase3')


def one(variant,mature,saving):
    if variant=='reference':
        from research.phase3.reference import viewer
        from research.phase3.reference.engine import World
        from research.phase3.reference.storage import load,save
    else:
        from gnome_fortress import viewer
        from gnome_fortress.engine import World
        from gnome_fortress.storage import load,save
    w=load('research/phase2/data/endurance/seed-01/final.sqlite') if mature else World(11)
    before=fingerprint(w);draws=[];finish=threading.Event();draw_duration=[];latencies=[]
    base=viewer.Observer
    class Paused(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.paused=True;self.save_requested=saving
        def handle(self,events):
            for e in events:
                if hasattr(e,'sent_at'):latencies.append(time.perf_counter()-e.sent_at)
            super().handle(events)
        def draw(self):
            t=time.perf_counter();draws.append(t);super().draw();draw_duration.append(time.perf_counter()-t)
    viewer.Observer=Paused
    def callback(world,path):
        value=save(world,path);finish.set();return value
    def inputs():
        import pygame
        while not finish.wait(.2):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB,sent_at=time.perf_counter()))
    poster=threading.Thread(target=inputs,daemon=True) if saving else None
    if poster:poster.start()
    start=time.perf_counter();cpu=time.process_time()
    stop=lambda: finish.is_set() if saving else time.perf_counter()-start>=2
    viewer.run(w,ROOT/'data/observer-save.sqlite',callback,checkpoint_ticks=1000000000,stop_requested=stop)
    elapsed=time.perf_counter()-start;cpu_elapsed=time.process_time()-cpu
    assert fingerprint(w)==before
    if saving:
        assert len(draws)>=3 and len(latencies)>=3
        poster.join(timeout=2)
    row=dict(variant=variant,mature=mature,saving=saving,wall_seconds=elapsed,
        cpu_seconds=cpu_elapsed,draws=len(draws),
        cpu_percent_one_core=cpu_elapsed/elapsed*100,
        input_events=len(latencies),maximum_input_latency_seconds=max(latencies,default=0),
        maximum_draw_gap_seconds=max((b-a for a,b in zip(draws,draws[1:])),default=0),
        maximum_draw_seconds=max(draw_duration,default=0),exact_unchanged_state=True,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        note='SDL dummy; actual observer loop; paused; no desktop or GPU assertion')
    path=ROOT/f'observer-{variant}-{int(mature)}-{int(saving)}.json'
    path.write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--variant',choices=('reference','optimized'))
    p.add_argument('--mature',action='store_true');p.add_argument('--saving',action='store_true');a=p.parse_args()
    if a.variant:one(a.variant,a.mature,a.saving);return
    (ROOT/'observer-manifest.json').write_text(json.dumps(dict(code_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list(Path('gnome_fortress').glob('*.py'))+[Path(__file__)])}),indent=2)+'\n')
    for mature in (False,True):
        for variant in ('reference','optimized'):
            command=[sys.executable,'-m','research.phase3_observer','--variant',variant]
            if mature:command.append('--mature')
            subprocess.run(command,check=True)
    subprocess.run([sys.executable,'-m','research.phase3_observer','--variant','optimized','--mature','--saving'],check=True)

if __name__=='__main__':main()
