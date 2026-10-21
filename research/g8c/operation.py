"""Real bounded Pygame operation, private worlds only; no human-playtest claim."""
import argparse,gc,hashlib,json,multiprocessing,os,pickle,resource,tempfile,threading,time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.reduction import ForkingPickler
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker,_writer_init
from gnome_fortress.chronicle import PreparedPayload
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_encoding import canonical_payload
from gnome_fortress.game_session import game_session
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.god_viewer import run

_calls=0;_restore_seconds=0.;_fail_second=False


def child_init(fail_second):
 global _fail_second
 _writer_init();_fail_second=fail_second;restore=PreparedPayload.restore
 def measured(self):
  global _restore_seconds
  t=time.perf_counter()
  try:return restore(self)
  finally:_restore_seconds=time.perf_counter()-t
 PreparedPayload.restore=measured


def child_save(w,path):
 global _calls
 _calls+=1
 if _fail_second and _calls==2:raise OSError('controlled G8C save failure; explicit retry required')
 result=save_game(w,path)
 result.update(reconstruction_seconds=_restore_seconds,child_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 return result


def digest(w):return hashlib.sha256(canonical_payload(w).encode()).hexdigest()


def main():
 p=argparse.ArgumentParser();p.add_argument('--scale',choices=('26000','player'),required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--cold',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 giant=a.scale=='player';start=time.perf_counter()
 w=load_game('/tmp/gnome-deep-time/player-copy.g5.sqlite') if giant else pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes())
 expected=digest(w);initial_tick=w.tick;print('loaded',a.scale,initial_tick,time.perf_counter()-start,flush=True)
 frames=[];preparation=[];captures=[];completions=[];feeders=[];collections=[];views=[];drains=[];stage='idle';starts={}
 def gc_callback(phase,info):
  key=(threading.get_ident(),info['generation'])
  if phase=='start':starts[key]=(time.perf_counter(),stage)
  else:
   t,context=starts.pop(key);collections.append(dict(start=t,end=time.perf_counter(),stage=context,generation=info['generation'],thread=threading.current_thread().name))
 gc.callbacks.append(gc_callback)
 original_dumps=ForkingPickler.dumps
 def dumps(cls,obj,protocol=None):
  t=time.perf_counter();data=original_dumps(obj,protocol)
  if threading.current_thread().name=='QueueFeederThread':feeders.append(dict(start=t,end=time.perf_counter(),bytes=len(data)))
  return data
 ForkingPickler.dumps=classmethod(dumps)
 class Worker(TerrainCheckpointWorker):
  @staticmethod
  def _new_pool():return ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'),initializer=child_init,initargs=(not giant,))
  def prepare(self,w,budget=.004):
   nonlocal stage
   stage='prepare';t=time.perf_counter();cpu=time.thread_time();result=super().prepare(w,budget)
   preparation.append(dict(ms=(time.perf_counter()-t)*1000,cpu_ms=(time.thread_time()-cpu)*1000,events=self.chronicle.prepared,dead=len(self.chronicle.dead)));stage='idle';return result
  def start(self,w,path):
   nonlocal stage
   stage='capture';self.sent=time.perf_counter();super().start(w,path)
   captures.append(dict(tick=w.tick,start=self.sent,ms=(time.perf_counter()-self.sent)*1000));stage='idle'
  def poll(self):
   result=super().poll()
   if result:
    result['pipeline_seconds']=time.perf_counter()-self.sent;result['completed_at']=time.perf_counter();completions.append(result)
    if len(completions)==1 and not a.cold:assert result['digest']==expected and result['tick']==initial_tick
    print('completed',a.scale,result['tick'],result['pipeline_seconds'],flush=True)
   return result
  def close(self):
   t=time.perf_counter();had_pending=self.pending
   try:return super().close()
   finally:drains.append(dict(seconds=time.perf_counter()-t,pending=had_pending))
 worker=Worker(child_save)
 # Explicit warm-session test. The cold/preparing owner-loop is exercised in a
 # separate bounded trace; this preparation phase is reported, never hidden.
 t=time.perf_counter()
 if not a.cold:
  while not worker.prepared_for(w):worker.prepare(w)
 warmup_seconds=time.perf_counter()-t;warmup_count=len(preparation);print('prepared',a.scale,warmup_seconds,flush=True)
 class View(LivingObserver):
  def __init__(self,*args):
   super().__init__(*args,window_size=(1280,720));views.append(self);self.previous=time.perf_counter();self.tested=False;self.retried=False;self.frame=None
   self.select_individual(min(w.living(),key=lambda x:(x.age,x.id)).id);self.toggle_follow();self.action('decision-observe');self.navigate('decisions');self.save_requested=True
  def handle(self,events):
   now=time.perf_counter();self.frame=dict(start=now,gap_ms=(now-self.previous)*1000,tick=w.tick,pending=getattr(self,'checkpoint_pending',False));frames.append(self.frame);self.previous=now
   super().handle(events)
   if self.frame['pending'] and not self.tested:
    self.tested=True;assert self.follow_id==self.selected and self.decisions.enabled
    if not a.cold:super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)])
    self.action('advisor');self.advisor.choose('1',w,self.selected,self.presentation);self.advisor.open=False
    self.navigate('terrain');self.set_mode('rain');self.pointer=self.viewport.center
    super().handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.pointer)])
    self.set_mode(None);self.navigate('decisions')
    self.draw();pygame.image.save(self.screen,str(a.out/f'{a.scale}-saving.png'))
   if getattr(self,'save_error',False) and not self.retried:
    self.retried=True;super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_s),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)])
   if len(completions)>=(1 if giant else 2):super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
  def advance(self,seconds):
   nonlocal stage
   stage='simulation';t=time.perf_counter();super().advance(seconds);self.frame['simulation_ms']=(time.perf_counter()-t)*1000;stage='idle'
  def draw(self):
   nonlocal stage
   stage='render';t=time.perf_counter();super().draw()
   if self.frame is not None:self.frame['render_ms']=(time.perf_counter()-t)*1000
   stage='idle'
 with tempfile.TemporaryDirectory(prefix='g8c-operational-') as temp:
  path=Path(temp)/'isolated.g5.sqlite'
  with game_session(path):
   # First writer creates a fresh, isolated complete file at the exact original T.
   run(w,path,child_save,checkpoint_ticks=60,max_frames=15000 if giant else 3000,rate=30,paused=not a.cold,observer_class=View,worker_class=lambda callback:worker)
   assert views[0].tested and completions and (giant or views[0].retried)
   assert not getattr(views[0],'save_error',False)
   t=time.perf_counter();final=save_game(w,path);shutdown_seconds=time.perf_counter()-t
   print('final saved',a.scale,w.tick,shutdown_seconds,flush=True)
   loaded=load_game(path);assert digest(loaded)==digest(w)==final['digest']
   loaded.step(20);w.step(20);assert digest(loaded)==digest(w)
 gc.callbacks.remove(gc_callback);ForkingPickler.dumps=original_dumps
 result=dict(scale=a.scale,cold=a.cold,driver=os.environ['SDL_VIDEODRIVER'],human_playtest=False,initial_tick=initial_tick,initial_digest=expected,
  warmup_seconds=warmup_seconds,warmup_calls=warmup_count,frames=frames,preparation=preparation,captures=captures,completions=completions,drains=drains,
  feeder=feeders,gc=collections,exit_saved_tick=final['tick'],shutdown_seconds=shutdown_seconds,exact_continuation=True,
  retried=views[0].retried,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
 (a.out/f'{a.scale}.json').write_text(json.dumps(result,indent=2)+'\n');print('exact complete',a.scale,flush=True)

if __name__=='__main__':main()
