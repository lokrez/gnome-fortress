"""Bounded matched G8B throughput, trace, journal drawing and warm capture probes."""
import argparse,gc,json,os,pickle,resource,statistics,subprocess,time,types
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.decision_observation import DecisionObservation
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.chronicle import Chronicle


def accepted():
    modules=[]
    for name in ('engine','terrain_game'):
        source=subprocess.check_output(['git','show',f'bf6e5568056e75f07cd7b9d468a592fc5e5abf6f:gnome_fortress/{name}.py'],text=True)
        m=types.ModuleType('gnome_fortress._g8b_reference_'+name);m.__package__='gnome_fortress'
        import sys;sys.modules[m.__name__]=m
        exec(compile(source,'<accepted '+name+'>','exec'),m.__dict__);modules.append(m)
    modules[1].World=modules[0].World
    return modules[1].TerrainWorld


def summary(samples):
    return dict(median_ms=statistics.median(samples),worst_ms=max(samples),samples_ms=samples)


def main():
    out=Path('docs/g8b/evidence/profile.json');rows=[];reference=accepted()
    fixtures=Path('/tmp/gnome-g8a2-generated-fixtures')
    for tick in (0,3000,10000,26000):
        initial=TerrainWorld() if tick==0 else pickle.loads((fixtures/f'{tick}.pickle').read_bytes())
        blob=pickle.dumps(initial,protocol=5);identity=min(initial.living(),key=lambda a:(a.age,a.id)).id;modes={};digests=[]
        measurements={mode:dict(samples=[],steps=[],decisions=0,trace_bytes=0)
                      for mode in ('reference','disabled','observed')}
        order=['reference','disabled','observed']
        for trial in range(3):
            for mode in order[trial:]+order[:trial]:
                m=measurements[mode];w=pickle.loads(blob)
                if mode=='reference':w.__class__=reference
                o=DecisionObservation()
                if mode=='observed':o.start(w,identity)
                gc.collect();start=time.perf_counter()
                for _ in range(180):
                    t=time.perf_counter();w.step();m['steps'].append((time.perf_counter()-t)*1000)
                    if o.records and o.records[-1]['tick']==w.tick and o.records[-1]['scheduled']:m['decisions']+=1
                m['samples'].append((time.perf_counter()-start)*1000)
                if mode=='observed':m['trace_bytes']=len(json.dumps(list(o.records)))
                digests.append(w.digest())
        for mode,m in measurements.items():
            modes[mode]=dict(**summary(m['samples']),step=summary(m['steps']),
                            decisions=m['decisions'],trace_json_bytes=m['trace_bytes'])
        assert len(set(digests))==1
        # Warm Chronicle and drawing measured separately from throughput.
        w=pickle.loads(blob);o=DecisionObservation();o.start(w,identity);cache=Chronicle()
        cache.prepare(w)
        while len(w.events)-cache.prepared>=128 or cache.dead_queue:
            cache.prepare(w)
        w.step(60);cache.prepare(w);warm=[]
        for _ in range(7):
            t=time.perf_counter();payload=cache.detach(w);warm.append((time.perf_counter()-t)*1000)
        v=LivingObserver(w,paused=True,window_size=(1280,720));v.select_individual(identity)
        v.decisions.stop(w);v.decisions=o;v.navigate('decisions');v.decision_details=True;v.draw()
        draw=[]
        before=w.digest()
        for _ in range(60):
            t=time.perf_counter();v.draw();draw.append((time.perf_counter()-t)*1000)
        assert w.digest()==before
        pygame.quit()
        row=dict(tick=tick,identity=identity,living=len(initial._living_agents),retained=len(initial.agents),
                 events=len(initial.events),modes=modes,exact=True,warm_capture=summary(warm),
                 drawing=summary(draw),hot_bytes=len(payload.hot),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        rows.append(row);out.write_text(json.dumps(dict(protocol='Seed-1 fixtures; three counterbalanced 180-tick trials per condition; youngest living ID (age, ID); 60 journal draws; seven warm captures.',rows=rows),indent=2)+'\n')
        print(tick,{k:round(v['median_ms'],2) for k,v in modes.items()},'warm',round(statistics.median(warm),2),flush=True)


if __name__=='__main__':main()
