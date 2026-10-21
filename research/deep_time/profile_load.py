"""Cold object-graph load phases; private checkpoints, OS page cache uncontrolled."""
import argparse,json,resource,time
from pathlib import Path
from gnome_fortress import terrain_storage as storage
from gnome_fortress.terrain_game import TerrainWorld


def main():
 p=argparse.ArgumentParser();p.add_argument('--scale',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 path=Path('/tmp/gnome-deep-time')/('player-copy.g5.sqlite' if a.scale=='player' else f'fixture-{a.scale}.g5.sqlite')
 metrics={};parse=storage.json.loads;construct=TerrainWorld.from_state.__func__;validate=TerrainWorld.validate
 def timed(label,fn,*args,**kwargs):
  t=time.perf_counter();cpu=time.process_time()
  try:return fn(*args,**kwargs)
  finally:metrics[label]=dict(wall_seconds=time.perf_counter()-t,cpu_seconds=time.process_time()-cpu)
 def loads(*args,**kw):return timed('json_parse',parse,*args,**kw)
 def from_state(cls,*args,**kw):return timed('reconstruction_including_validation',construct,cls,*args,**kw)
 def check(self):return timed('validation',validate,self)
 storage.json.loads=loads;TerrainWorld.from_state=classmethod(from_state);TerrainWorld.validate=check
 t=time.perf_counter();w=storage.load_game(path);elapsed=time.perf_counter()-t
 result=dict(scale=a.scale,tick=w.tick,agents=len(w.agents),events=len(w.events),load_seconds=elapsed,phases=metrics,
             peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(result,flush=True)

if __name__=='__main__':main()
