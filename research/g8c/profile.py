"""Read-only private fixtures; instrument actual Chronicle units and GC overlap."""
import argparse,cProfile,gc,io,json,pickle,pstats,resource,time
from collections import defaultdict
from pathlib import Path
from gnome_fortress import chronicle as module
from gnome_fortress.model import Agent
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import load_game
from gnome_fortress.terrain_checkpoint import capture_snapshot


def main():
 p=argparse.ArgumentParser();p.add_argument('--scale',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 start=time.perf_counter();w=load_game('/tmp/gnome-deep-time/player-copy.g5.sqlite') if a.scale=='player' else TerrainWorld(1) if a.scale=='0' else pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes())
 result=dict(scale=a.scale,tick=w.tick,agents=len(w.agents),events=len(w.events),load_seconds=time.perf_counter()-start)
 print('loaded',a.scale,flush=True)
 gc_events=[];beginnings={}
 def callback(phase,info):
  if phase=='start':beginnings[info['generation']]=time.perf_counter()
  else:gc_events.append(dict(start=beginnings.pop(info['generation']),end=time.perf_counter(),generation=info['generation'],collected=info['collected']))
 gc.callbacks.append(callback)
 stats=defaultdict(lambda:dict(calls=0,seconds=0.,worst_ms=0.));slow=[]
 def measured(label,fn,*args,**kw):
  t=time.perf_counter()
  try:return fn(*args,**kw)
  finally:
   seconds=time.perf_counter()-t;s=stats[label];s['calls']+=1;s['seconds']+=seconds;s['worst_ms']=max(s['worst_ms'],seconds*1000)
   if seconds>.016:slow.append(dict(label=label,ms=seconds*1000,start=t,end=t+seconds))
 bind=module.Chronicle.bind;create=module.Block.__init__;encode=module.Block.encode
 module.Chronicle.bind=lambda self,*args,**kw:measured('bind',bind,self,*args,**kw)
 def make(self,records):
  self._bench_kind='dead' if isinstance(records[0],Agent) else 'events'
  return measured(self._bench_kind+'_create_track',create,self,records)
 module.Block.__init__=make
 module.Block.encode=lambda self:measured(getattr(self,'_bench_kind','unknown')+'_encode',encode,self)
 t=time.perf_counter();cold=capture_snapshot(w);result['cold_full_ms']=(time.perf_counter()-t)*1000;result['cold_bytes']=len(cold);del cold
 cache=module.Chronicle();samples=[];start=time.perf_counter()
 while True:
  t=time.perf_counter();cpu=time.thread_time();elapsed=cache.prepare(w);end=time.perf_counter()
  samples.append(dict(ms=elapsed*1000,cpu_ms=(time.thread_time()-cpu)*1000,start=t,end=end,events=cache.prepared,dead=len(cache.dead)))
  if len(w.events)-cache.prepared<128 and not cache.dead_queue:break
 result['preparation_seconds']=time.perf_counter()-start;result['preparation']=samples
 result['units']=dict(stats);stats.clear()
 cache.detach(w);result['instrumented_warm_units']=dict(stats)
 # Timers on every tiny cached encode otherwise distort the warm distribution.
 module.Chronicle.bind=bind;module.Block.encode=encode
 warm=[]
 for _ in range(15):
  t=time.perf_counter();bundle=cache.detach(w);warm.append((time.perf_counter()-t)*1000)
 result['warm_ms']=warm
 profile=cProfile.Profile();profile.enable();cache.detach(w);profile.disable();s=io.StringIO();pstats.Stats(profile,stream=s).sort_stats('cumulative').print_stats(35);(a.out/f'{a.scale}-detach.txt').write_text(s.getvalue())
 t=time.perf_counter();blob=pickle.dumps(bundle,protocol=5);result['feeder_pickle_ms']=(time.perf_counter()-t)*1000;result['bytes']=len(blob);del blob
 result['gc']=gc_events;result['slow_units']=slow;result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 gc.callbacks.remove(callback)
 (a.out/f'{a.scale}.json').write_text(json.dumps(result,indent=2)+'\n');print(a.scale,result['preparation_seconds'],max(r['ms'] for r in samples),warm,flush=True)

if __name__=='__main__':main()
