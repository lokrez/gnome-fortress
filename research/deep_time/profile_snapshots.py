"""Read private fixtures only; measure unchanged Chronicle at real history scales."""
import argparse,gc,json,pickle,resource,time
from pathlib import Path
from gnome_fortress.chronicle import Chronicle
from gnome_fortress.terrain_checkpoint import capture_snapshot
from gnome_fortress.terrain_storage import load_game


def main():
 p=argparse.ArgumentParser();p.add_argument('--scale',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 t=time.perf_counter()
 w=load_game('/tmp/gnome-deep-time/player-copy.g5.sqlite') if a.scale=='player' else pickle.loads(Path(f'/tmp/gnome-g8a2-generated-fixtures/{a.scale}.pickle').read_bytes())
 result=dict(scale=a.scale,tick=w.tick,agents=len(w.agents),events=len(w.events),load_seconds=time.perf_counter()-t)
 t=time.perf_counter();blob=capture_snapshot(w);result['cold_full_capture_ms']=(time.perf_counter()-t)*1000;result['cold_bytes']=len(blob);del blob;gc.collect()
 cache=Chronicle();slices=[];start=time.perf_counter()
 while True:
  slices.append(cache.prepare(w)*1000)
  if len(w.events)-cache.prepared<128 and not cache.dead_queue:break
 result['preparation_seconds']=time.perf_counter()-start
 result['preparation_slices']=len(slices);result['preparation_max_ms']=max(slices)
 samples=[]
 for _ in range(7):
  t=time.perf_counter();bundle=cache.detach(w);samples.append((time.perf_counter()-t)*1000)
 result['warm_detach_ms']=samples
 t=time.perf_counter();blob=pickle.dumps(bundle,protocol=5);result['feeder_pickle_seconds']=time.perf_counter()-t;result['segmented_bytes']=len(blob);del blob
 result['cached_event_bytes']=sum(len(b.payload) for b in cache.blocks)
 result['cached_dead_bytes']=sum(len(b.payload) for b in cache.dead.values())
 result['hot_bytes']=len(bundle.hot);result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
