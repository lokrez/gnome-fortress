"""Predeclared bounded matched-world G5–G7 comparisons, not outcome tuning."""
import argparse
from collections import Counter
from dataclasses import asdict
import csv
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

from gnome_fortress.engine import World
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_presentation import TerrainIndex


def canonical(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def plan(world,condition):
    land=min(((x,y) for y,row in enumerate(world.cells) for x,c in enumerate(row) if c.terrain in ('grass','forest')),
             key=lambda xy:(abs(xy[0]-world.width//2)+abs(xy[1]-world.height//2),xy[1],xy[0]))
    spring=next((x,y) for y,row in enumerate(world.cells) for x,c in enumerate(row) if c.terrain=='rock' and
                any(world.cell(nx,ny).terrain in ('grass','forest','hazard') for nx,ny in world.neighbors(x,y)))
    def item(tick,kind,xy,radius,duration=None):return dict(tick=tick,kind=kind,x=xy[0],y=xy[1],radius=radius,duration=duration)
    rupture=item(99,'rupture',land,2);rewild=item(399,'rewild',land,2);well=item(199,'wellspring',spring,0)
    if condition=='A':return []
    elif condition=='B':return [rupture]
    elif condition=='C':return [rupture,rewild]
    elif condition=='D':return [well]
    elif condition=='E':return [item(49,'rain',land,5,300),rupture,item(249,'drought',land,3,200),rewild,item(499,'wellspring',spring,0)]
    raise ValueError('Unknown condition')


def simulate(seed,ticks,schedule,checkpoint=None,assert_initial=True):
    world=TerrainWorld(seed);untouched=TerrainWorld(seed) if schedule and assert_initial else None
    by_tick={}
    for action in schedule:by_tick.setdefault(action['tick'],[]).append(action)
    midpoint=False;before_equal=not schedule
    while world.tick<ticks and not world.extinct:
        if untouched is not None:
            assert world.state()==untouched.state()
        for action in by_tick.get(world.tick,[]):
            if untouched is not None:
                before_equal=True;untouched=None
            world.request(action['kind'],action['x'],action['y'],action['radius'],action['duration'])
        if checkpoint is not None and world.tick==250:
            save_game(world,checkpoint);loaded=load_game(checkpoint)
            assert world.state()==loaded.state();world=loaded;midpoint=True
        world.step()
        if untouched is not None:untouched.step()
    world.validate()
    return world,midpoint,before_equal


def worker(seed,condition,ticks,output):
    output.mkdir(parents=True,exist_ok=True)
    schedule=plan(TerrainWorld(seed),condition);cpu=time.process_time();started=time.perf_counter()
    with tempfile.TemporaryDirectory() as folder:
        a,midpoint,before_equal=simulate(seed,ticks,schedule,Path(folder)/'midpoint.g5.sqlite')
        primary=time.perf_counter()-started
        started=time.perf_counter();b,_,_=simulate(seed,ticks,schedule,assert_initial=False)
        replay_seconds=time.perf_counter()-started
        assert a.state()==b.state()
        if condition=='A':
            from research.phase3.reference.engine import World as Reference
            reference=Reference(seed);reference.step(a.tick)
            assert World.state(a)==reference.state()
        primary_state=World.state(a);reference_equal=True if condition=='A' else None
        save_metrics=save_game(a,Path(folder)/'final.g5.sqlite');loaded=load_game(Path(folder)/'final.g5.sqlite')
        assert a.state()==loaded.state()
        a.step(20);loaded.step(20);assert a.state()==loaded.state()
    # Summaries describe the pre-continuation endpoint, not the additional 20 ticks.
    final=TerrainWorld.from_state({**primary_state,'game':b.state()['game']})
    terrain=Counter(c.terrain for row in final.cells for c in row)
    deaths=Counter(e.detail['cause'] for e in final.events if e.kind=='death')
    hazards=[e for e in final.events if e.kind=='hazard'];index=TerrainIndex(final)
    result=dict(seed=seed,condition=condition,ticks=final.tick,schedule=schedule,
        interventions=[asdict(p) for p in final.interventions],terrain=dict(sorted(terrain.items())),
        food_stock=sum(c.food for row in final.cells for c in row),living=len(final._living_agents),
        born_total=len(final.agents),offspring_births=len(final.agents)-60,deaths=sum(deaths.values()),
        deaths_by_cause=dict(sorted(deaths.items())),hazard_entries=len(hazards),
        transformed_hazard_entries=sum(index.hazard_provenance(e) is not None for e in hazards),
        terrain_summary=index.summary(),state_digest=final.digest(),rng_digest=canonical(final.rng.getstate()),
        primary_seconds=primary,primary_ticks_per_second=final.tick/primary,replay_seconds=replay_seconds,
        total_cpu_seconds=time.process_time()-cpu,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        midpoint_tick=250,midpoint_exact=midpoint,before_first_request_exact=before_equal,
        independent_replay_exact=True,final_save_metrics=save_metrics,final_save_load_plus20_exact=True,
        untouched_reference_exact=reference_equal)
    (output/f'{condition}-seed-{seed}-ticks-{ticks}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('interventions','schedule')},sort_keys=True))
    return result


def write_csv(rows,output):
    keys=['seed','condition','ticks','living','born_total','offspring_births','deaths','food_stock','hazard_entries',
          'transformed_hazard_entries','primary_seconds','primary_ticks_per_second','peak_rss_mib','state_digest','rng_digest',
          'midpoint_exact','independent_replay_exact','final_save_load_plus20_exact','untouched_reference_exact','death_hazard','death_starvation','death_dehydration','death_old_age']
    with (output/'summary.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=keys,lineterminator='\n');writer.writeheader()
        for r in rows:
            flat={**r,**{'death_'+cause:r['deaths_by_cause'].get(cause,0) for cause in ('hazard','starvation','dehydration','old_age')}}
            writer.writerow({k:flat[k] for k in keys})


def campaign(output,ticks=3000):
    output.mkdir(parents=True,exist_ok=True);rows=[]
    for seed in (1,2,3):
        for condition in 'ABCDE':
            command=[sys.executable,'-m','research.overnight_study','--worker','--seed',str(seed),'--condition',condition,'--ticks',str(ticks),'--output',str(output)]
            completed=subprocess.run(command,text=True,capture_output=True,check=True)
            row=json.loads(completed.stdout);rows.append(row)
            print(f"seed {seed} {condition}: living {row['living']}, primary {row['primary_seconds']:.2f}s, replay exact",flush=True)
    write_csv(rows,output)
    (output/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--worker',action='store_true');p.add_argument('--seed',type=int,default=1)
    p.add_argument('--condition',choices=list('ABCDE'),default='E');p.add_argument('--ticks',type=int,default=3000)
    args=p.parse_args()
    if args.ticks<251:p.error('At least 251 ticks required for midpoint verification')
    if args.worker:worker(args.seed,args.condition,args.ticks,args.output)
    else:campaign(args.output,args.ticks)
