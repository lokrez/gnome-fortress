"""Actual launcher finalization on ONE private copy, no simulation advancement."""
import argparse,hashlib,json,resource,subprocess,time,types
from pathlib import Path
from gnome_fortress import god_world,terrain_storage
from gnome_fortress.game_session import game_session


def reference(name):
 m=types.ModuleType('gnome_fortress._deep_time_'+name);m.__package__='gnome_fortress';m.__file__=str(Path(god_world.__file__).with_name(name+'.py'))
 source=subprocess.check_output(['git','show','72a101727d84a65dd49186503eea765825fa0987:gnome_fortress/'+name+'.py'])
 exec(compile(source,'<accepted '+name+'>','exec'),m.__dict__);return m


def main():
 p=argparse.ArgumentParser();p.add_argument('--reference',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 launcher=reference('god_world') if a.reference else god_world
 storage=reference('terrain_storage') if a.reference else terrain_storage
 metrics={};world=[];hash_times=[];original_sha=hashlib.sha256
 def sha(data=b'',*args,**kwargs):
  t=time.perf_counter()
  try:return original_sha(data,*args,**kwargs)
  finally:hash_times.append(dict(bytes=len(data),seconds=time.perf_counter()-t))
 hashlib.sha256=sha
 def load(path):
  t=time.perf_counter();w=storage.recover_game(path);metrics['load_seconds']=time.perf_counter()-t
  # No retained second world; this list references the single launch object.
  world.append(w);return w
 def save(w,path):
  t=time.perf_counter();result=storage.save_game(w,path);metrics['final_save_seconds']=time.perf_counter()-t
  metrics['committed_digest']=result.get('digest');metrics['save_finished_at']=time.perf_counter();return result
 launcher.recover_game=load;launcher.save_game=save
 args=argparse.Namespace(new=False,import_legacy=None,seed=1,headless=True,ticks=0,checkpoint_every=300)
 path=Path('/tmp/gnome-deep-time/player-copy.g5.sqlite');assert path.is_file()
 args.db=path
 with game_session(path):
  start=time.perf_counter();launcher._launch(args,p,path);end=time.perf_counter()
 metrics['load_save_summary_total_seconds']=end-start
 metrics['post_commit_summary_seconds']=end-metrics.pop('save_finished_at')
 metrics['shutdown_excluding_load_seconds']=end-start-metrics['load_seconds']
 metrics['sha256_calls']=hash_times
 metrics.update(reference=a.reference,tick=world[0].tick,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                minor_faults=resource.getrusage(resource.RUSAGE_SELF).ru_minflt,major_faults=resource.getrusage(resource.RUSAGE_SELF).ru_majflt)
 a.out.write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics,indent=2),flush=True)

if __name__=='__main__':main()
