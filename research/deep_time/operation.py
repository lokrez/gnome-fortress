"""Same real Pygame/Saveguard workload, reference versus optimized writer.

SDL dummy is an executable renderer/input check, not a human smoothness playtest.
"""
import argparse,json,os,pickle,resource,subprocess,tempfile,time,types
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.game_session import game_session
from gnome_fortress.god_viewer import run


def reference_save(w,path):
 m=types.ModuleType('gnome_fortress._deep_time_old_storage');m.__package__='gnome_fortress'
 source=subprocess.check_output(['git','show','72a101727d84a65dd49186503eea765825fa0987:gnome_fortress/terrain_storage.py'])
 exec(compile(source,'<accepted storage>','exec'),m.__dict__)
 return m.save_game(w,path)


def main():
 p=argparse.ArgumentParser();p.add_argument('--reference',action='store_true');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 writer=reference_save if a.reference else save_game
 w=pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes())
 frames=[];captures=[];completed=[];views=[];preparations=[]
 class Worker(TerrainCheckpointWorker):
  def prepare(self,w,budget=.004):
   t=super().prepare(w,budget);preparations.append(t*1000);return t
  def start(self,w,path):
   t=time.perf_counter();self.sent_at=t;super().start(w,path);captures.append(dict(tick=w.tick,ms=(time.perf_counter()-t)*1000))
  def poll(self):
   result=super().poll()
   if result:
    result['pipeline_seconds']=time.perf_counter()-self.sent_at
    result['pipeline_minus_writer_seconds']=result['pipeline_seconds']-result['seconds']
    completed.append(result)
   return result
 class View(LivingObserver):
  def __init__(self,*args):
   super().__init__(*args,window_size=(1280,720));views.append(self);self.previous=time.perf_counter();self.checked=False
   self.select_individual(min(w.living(),key=lambda x:(x.age,x.id)).id);self.toggle_follow();self.action('decision-observe')
  def handle(self,events):
   now=time.perf_counter();frames.append(dict(tick=w.tick,ms=(now-self.previous)*1000,pending=getattr(self,'checkpoint_pending',False)));self.previous=now
   super().handle(events)
   if getattr(self,'checkpoint_pending',False) and not self.checked:
    self.checked=True;assert self.follow_id==self.selected and self.decisions.enabled
    self.action('advisor');self.advisor.choose('1',w,self.selected,self.presentation);self.advisor.open=False;self.navigate('decisions')
    # Cast a real predetermined request after capture, independent of frame rate.
    # Activation waits until the next complete tick.
    self.draw();pygame.image.save(self.screen,str(a.out.with_suffix('.png')))
   if completed:super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
 with tempfile.TemporaryDirectory(prefix='deep-time-operation-') as temp:
  path=Path(temp)/'operation.g5.sqlite'
  with game_session(path):
   writer(w,path)
   run(w,path,writer,checkpoint_ticks=600,max_frames=3000,rate=30,observer_class=View,worker_class=Worker)
   assert completed and views[0].checked and not getattr(views[0],'save_error',False)
   t=time.perf_counter();writer(w,path);shutdown_seconds=time.perf_counter()-t
   loaded=load_game(path);assert loaded.state()==w.state()
   loaded.step(30);w.step(30);assert loaded.state()==w.state()
 gaps=sorted(f['ms'] for f in frames)
 result=dict(reference=a.reference,driver=os.environ['SDL_VIDEODRIVER'],human_playtest=False,
  tick=w.tick,frames=frames,captures=captures,completions=completed,preparation_max_ms=max(preparations),
  gap_p95_ms=gaps[int((len(gaps)-1)*.95)],gap_p99_ms=gaps[int((len(gaps)-1)*.99)],max_gap_ms=max(gaps),
  final_save_seconds=shutdown_seconds,continuation_exact=True,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
  child_peak_rss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
 a.out.write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k not in ('frames','completions')})

if __name__=='__main__':main()
