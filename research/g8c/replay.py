"""No preparation vs accepted Chronicle vs G8C, exact canonical/RNG boundaries."""
import hashlib,json,subprocess,sys,tempfile,types
from pathlib import Path
from gnome_fortress.chronicle import Chronicle
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_encoding import canonical_payload
from gnome_fortress.terrain_storage import save_game,load_game


def reference():
 m=types.ModuleType('gnome_fortress._g8c_reference');m.__package__='gnome_fortress';sys.modules[m.__name__]=m
 source=subprocess.check_output(['git','show','c88b217:gnome_fortress/chronicle.py'])
 exec(compile(source,'<accepted Chronicle>','exec'),m.__dict__);return m.Chronicle


def main():
 rows=[];Reference=reference()
 for seed in (1,7,42):
  worlds=[TerrainWorld(seed) for _ in range(3)];caches=[None,Reference(),Chronicle()]
  rock=next((x,y) for y,row in enumerate(worlds[0].cells) for x,c in enumerate(row) if c.terrain=='rock')
  schedule={0:[('rain',5,5)],2:[('drought',5,5)],9:[('rupture',5,5),('rewild',5,5)],
            18:[('wellspring',*rock),('wellspring',*rock)],37:[('rupture',5,5)],40:[('rewild',5,5)]}
  def request(w):
   for kind,x,y in schedule.get(w.tick,[]):w.request(kind,x,y)
  with tempfile.TemporaryDirectory(prefix='g8c-replay-') as temp:
   for tick in range(3001):
    for w in worlds:request(w)
    for w,c in zip(worlds,caches):
     if c:c.prepare(w,.001)
    if tick in (0,1,2,9,10,18,19,38,41,201,500,1600,3000):
     states=[canonical_payload(w) for w in worlds];assert states[0]==states[1]==states[2]
     assert worlds[0].rng.getstate()==worlds[1].rng.getstate()==worlds[2].rng.getstate()
     for w,c in zip(worlds[1:],caches[1:]):assert canonical_payload(c.detach(w).restore())==states[0]
     p=Path(temp)/'checkpoint.g5.sqlite';metrics=save_game(caches[2].detach(worlds[2]).restore(),p)
     restored=load_game(p);assert canonical_payload(restored)==states[0]
     control=TerrainWorld.from_state(worlds[0].state())
     for _ in range(20):
      for w in (restored,control):w.step();request(w)
     assert canonical_payload(restored)==canonical_payload(control)
     rows.append(dict(seed=seed,tick=tick,sha256=hashlib.sha256(states[0].encode()).hexdigest(),
         saved_sha256=metrics['digest'],living=len(worlds[0]._living_agents),born=len(worlds[0].agents),events=len(worlds[0].events)))
    if tick<3000:
     for w in worlds:w.step()
  print('replay seed',seed,flush=True)
 Path('docs/g8c/evidence/replay.json').write_text(json.dumps(dict(exact=True,reference='c88b217',rows=rows),indent=2)+'\n')

if __name__=='__main__':main()
