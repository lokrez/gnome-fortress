"""Prospective bounded starvation counters; real production rules and RNG.

Wrappers are research-only, never installed in gameplay. No full decision replay,
no per-tick biographies, no historical reconstruction from the player's save.
"""
import argparse,csv,json,pickle,time
from collections import Counter,defaultdict,deque
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from gnome_fortress.engine import World,TRAITS
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_encoding import canonical_payload
import hashlib

SEEDS=(1,7,42,77,2026,4096)


def digest(w):return hashlib.sha256(canonical_payload(w).encode()).hexdigest()


def fresh_counters():return dict(ticks=0,hungry=0,opportunities=0,hungry_opportunities=0,eats=0,moves=0,revisits=0,hazards=0,last_eat=None,path=deque(maxlen=16))


class Monitor:
 def __init__(self,w):
  self.w=w;self.count=Counter();self.groups=defaultdict(Counter);self.live={};self.examples=[];self.deaths=defaultdict(Counter)
  self.tile_ticks=Counter();self.tile_empty=Counter();self.tile_food=Counter();self.offsets={}
  self.event_cursor=len(w.events);self.founders={k:sum(a.traits[k] for a in w.agents.values())/60 for k in TRAITS};self.cohorts=[]
 def record(self,a):return self.live.setdefault(a.id,fresh_counters())
 def edible(self,a):
  radius=3+a.traits['vision']//25
  if radius not in self.offsets:self.offsets[radius]=[(dx,dy) for dy in range(-radius,radius+1) for dx in range(-radius,radius+1) if abs(dx)+abs(dy)<=radius]
  return any(0<=a.x+dx<self.w.width and 0<=a.y+dy<self.w.height and self.w.cell(a.x+dx,a.y+dy).food>=10 for dx,dy in self.offsets[radius])
 def scheduled(self,chosen):
  w=self.w;selected=set(chosen)
  for a in w._living_agents.values():
   r=self.record(a);r['ticks']+=1;self.count['living_tick_exposures']+=1
   if a.hunger<80:continue
   r['hungry']+=1;self.count['hungry_tick_exposures']+=1
   if a.hunger>=100:self.count['hunger_ge100_exposures']+=1
   awake=a.sleep_until<=w.tick;local=w.cell(a.x,a.y).food;visible=self.edible(a)
   flags=dict(hungry=1,assigned=int(a.id in selected),awake=int(awake),sleeping=int(not awake),
              local_edible=int(local>=10),visible_edible=int(visible),local_subthreshold=int(0<local<10))
   for key,value in flags.items():self.count['hungry_'+key]+=value
   for trait in ('vision','curiosity'):
    band=min(3,a.traits[trait]//25);g=self.groups[f'{trait}:{band}']
    for key,value in flags.items():g[key]+=value
   if a.id in selected:r['hungry_opportunities']+=1
  if w.tick%10==0:
   for y,row in enumerate(w.cells):
    for x,c in enumerate(row):
     if c.terrain not in ('grass','forest'):continue
     key=(x,y);self.tile_ticks[key]+=1;self.tile_empty[key]+=int(c.food<10);self.tile_food[key]+=c.food
 def decision(self,a,execute):
  r=self.record(a);r['opportunities']+=1;before=(a.x,a.y);hungry=a.hunger>=80
  local=self.w.cell(a.x,a.y).food;thirst=a.thirst;execute(a)
  action='move' if not a.alive and a.death_cause=='hazard' and (a.x,a.y)!=before else a.action
  self.count['actual_decisions']+=1;self.count['action_'+action]+=1
  if hungry:
   self.count['hungry_action_'+action]+=1
   if local>=10:
    self.count['hungry_edible_action_'+action]+=1
    if action=='drink':self.count['drink_preempts_available_food']+=1
  if a.action=='eat':r['eats']+=1;r['last_eat']=self.w.tick
  if (a.x,a.y)!=before:
   r['moves']+=1
   if (a.x,a.y) in r['path']:r['revisits']+=1;self.count['move_revisits_last16']+=1
   r['path'].append(before);self.count['moves']+=1
  if not a.alive:self.live.pop(a.id,None)
 def death(self,a,cause,execute):
  if not a.alive:return execute(a,cause)
  r=self.record(a);local=self.w.cell(a.x,a.y).food;visible=self.edible(a)
  immediate_hazard=bool(self.w.events and self.w.events[-1].kind=='hazard' and self.w.events[-1].actor==a.id and self.w.events[-1].tick==self.w.tick)
  d=self.deaths[cause];d['count']+=1;d['local_edible']+=int(local>=10);d['visible_edible']+=int(visible)
  d['prior_hazard']+=int(r['hazards']>0 or immediate_hazard);d['hungry_ticks']+=r['hungry'];d['hungry_opportunities']+=r['hungry_opportunities']
  d['eats']+=r['eats'];d['opportunities']+=r['opportunities'];d['hunger_sum']+=a.hunger;d['thirst_sum']+=a.thirst
  for trait in TRAITS:d[trait+'_sum']+=a.traits[trait]
  if len(self.examples)<128:
   self.examples.append(dict(tick=self.w.tick,identity=a.id,cause=cause,x=a.x,y=a.y,hunger=a.hunger,thirst=a.thirst,
       health=a.health,fatigue=a.fatigue,local_food=local,visible_edible=visible,traits=dict(a.traits),
       prior_hazard=r['hazards']>0 or immediate_hazard,**{k:v for k,v in r.items() if k!='path'}))
  execute(a,cause);self.live.pop(a.id,None)
 def after_tick(self):
  for index in range(self.event_cursor,len(self.w.events)):
   e=self.w.events[index]
   if e.kind=='birth' and e.detail.get('parents'):
    child=self.w.agents[e.actor];parents=[self.w.agents[p] for p in child.parents]
    self.count['observed_births']+=1
    for trait in TRAITS:
     total=sum(p.traits[trait] for p in parents)
     self.count['birth_parent_mid_sum_'+trait]+=total/2
     self.count['birth_rounding_sum_'+trait]+=total//2-total/2
     self.count['birth_child_sum_'+trait]+=child.traits[trait]
     self.count['birth_residual_sum_'+trait]+=child.traits[trait]-total//2
   if e.kind in ('hazard','sleep','wake'):self.count['event_'+e.kind]+=1
   if e.kind=='hazard' and e.actor in self.w._living_agents:self.record(self.w.agents[e.actor])['hazards']+=1
  self.event_cursor=len(self.w.events)
 def cohort(self):
  living=self.w.living();dead=[a for a in self.w.agents.values() if not a.alive]
  self.cohorts.append(dict(tick=self.w.tick,living=len(living),born=len(self.w.agents),deaths=len(dead),
    living_means={k:sum(a.traits[k] for a in living)/len(living) if living else None for k in TRAITS},
    death_causes=dict(Counter(a.death_cause for a in dead))))
 @contextmanager
 def install(self):
  original_schedule=World.schedule;original_decide=World.decide;original_kill=World.kill
  monitor=self
  def schedule(world):
   chosen=original_schedule(world)
   if world is monitor.w:monitor.scheduled(chosen)
   return chosen
  def decide(world,a):
   if world is monitor.w:return monitor.decision(a,lambda a:original_decide(world,a))
   return original_decide(world,a)
  def kill(world,a,cause):
   if world is monitor.w:return monitor.death(a,cause,lambda a,c:original_kill(world,a,c))
   return original_kill(world,a,cause)
  with patch.object(World,'schedule',schedule),patch.object(World,'decide',decide),patch.object(World,'kill',kill):yield
 def result(self,seconds):
  w=self.w;depth={}
  for a in w.agents.values():depth[a.id]=1+max((depth[p] for p in a.parents),default=-1)
  return dict(seed=w.seed,tick=w.tick,seconds=seconds,digest=digest(w),founder_means=self.founders,
    counts=dict(self.count),groups={k:dict(v) for k,v in self.groups.items()},deaths={k:dict(v) for k,v in self.deaths.items()},
    examples=self.examples,cohorts=self.cohorts,max_parent_depth=max(depth.values()),
    final_food=sum(c.food for row in w.cells for c in row),living=len(w._living_agents),total_born=len(w.agents),
    tiles=[dict(x=k[0],y=k[1],samples=v,below10=self.tile_empty[k],food_sum=self.tile_food[k]) for k,v in self.tile_ticks.items()])


def run(seed,horizon):
 w=TerrainWorld(seed);m=Monitor(w);m.cohort();start=time.perf_counter()
 with m.install():
  for tick in range(horizon):
   w.step();m.after_tick()
   if w.tick in (1000,3000,horizon):m.cohort()
   if w.extinct:break
 w.validate();return w,m.result(time.perf_counter()-start)


def main():
 p=argparse.ArgumentParser();p.add_argument('--pilot',action='store_true');p.add_argument('--out',type=Path,default=Path('docs/deep-time/evidence'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 if a.pilot:
  start=time.perf_counter();reference=TerrainWorld(1);reference.step(1000);baseline=time.perf_counter()-start
  observed,result=run(1,1000);assert digest(observed)==digest(reference)
  (a.out/'ecology-pilot.json').write_text(json.dumps(dict(baseline_seconds=baseline,instrumented=result,exact=True,
     estimate_six_10000_seconds=result['seconds']*60),indent=2)+'\n');print(baseline,result['seconds'],result['seconds']*60,flush=True)
 else:
  results=[]
  for seed in SEEDS:
   w,result=run(seed,10000);results.append(result)
   if seed==1:
    reference=TerrainWorld(seed);reference.step(10000)
    assert digest(reference)==result['digest']
    result['uninstrumented_replay_exact']=True
   (a.out/f'ecology-{seed}.json').write_text(json.dumps(result,indent=2)+'\n')
   print(seed,w.tick,len(w.agents),result['seconds'],flush=True)
  (a.out/'ecology.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
