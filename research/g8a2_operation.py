"""Bounded real-viewer mature-world operation with isolated failure/retry."""
import argparse,json,os,pickle,tempfile,time
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.game_session import game_session
from gnome_fortress.god_viewer import run

_calls=0

def save_once_failed(w,path):
    global _calls
    _calls+=1
    if _calls==2:raise OSError('controlled G8A.2 operational save failure; retry required')
    return save_game(w,path)


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('docs/g8a2/evidence'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    w=pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes())
    frames=[];captures=[];preparations=[];completed=[];workers=[];viewers=[]
    class Worker(TerrainCheckpointWorker):
        def __init__(self,*args):super().__init__(*args);workers.append(self)
        def prepare(self,w,budget=.004):
            t=super().prepare(w,budget);preparations.append(dict(tick=w.tick,ms=t*1000,prepared=self.chronicle.prepared,events=len(w.events),ready=len(w.events)-self.chronicle.prepared<128 and not self.chronicle.dead_queue,frame=viewers[-1].frame));return t
        def start(self,w,path):
            start=time.perf_counter();super().start(w,path);captures.append(dict(tick=w.tick,ms=(time.perf_counter()-start)*1000));self.sent_tick=w.tick
        def poll(self):
            result=super().poll()
            if result:completed.append(result)
            return result
    class View(LivingObserver):
        def __init__(self,*args):
            super().__init__(*args,window_size=(1280,720));self.previous=time.perf_counter();self.frame=0;self.retried=False;self.tested=False;viewers.append(self)
            self.toggle_follow()
        def handle(self,events):
            now=time.perf_counter();self.frame+=1
            frames.append(dict(frame=self.frame,tick=self.world.tick,gap_ms=(now-self.previous)*1000,pending=getattr(self,'checkpoint_pending',False)))
            self.previous=now;super().handle(events)
            if getattr(self,'checkpoint_pending',False) and not self.tested:
                # Navigation and a genuine queued environmental input during save.
                self.tested=True
                target=min(self.world.living(),key=lambda a:(a.age,a.id)).id
                self.select_individual(target);self.toggle_follow()
                assert self.follow_id==target
                self.action('advisor');self.advisor.choose('1',self.world,self.selected,self.presentation);self.advisor.open=False
                self.set_mode('rain');self.pointer=self.viewport.center
                super().handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.pointer)])
                self.set_mode(None)
                self.draw();pygame.image.save(self.screen,str(a.out/'mature-saving-active.png'))
            if getattr(self,'save_error',False) and not self.retried:
                self.retried=True;super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_s),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_SPACE)])
            if len(completed)>=3:
                pygame.image.save(self.screen,str(a.out/'mature-saving.png'))
                super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
    with tempfile.TemporaryDirectory(prefix='g8a2-operational-') as temporary:
        path=Path(temporary)/'mature.g5.sqlite'
        with game_session(path):
            save_game(w,path);run(w,path,save_once_failed,checkpoint_ticks=300,max_frames=6500,rate=15,observer_class=View,worker_class=Worker)
            assert len(completed)>=3 and viewers[0].retried and viewers[0].tested
            save_game(w,path);exit_saved_tick=w.tick;loaded=load_game(path);assert loaded.state()==w.state()
            loaded.step(30);w.step(30);assert loaded.state()==w.state()
    result=dict(driver=os.environ['SDL_VIDEODRIVER'],human_playtest=False,frames=frames,captures=captures,preparations=preparations,
        completions=completed,retried=viewers[0].retried,exit_saved_tick=exit_saved_tick,final_tick=w.tick,relaunch_continuation_exact=True,final_digest=w.digest())
    (a.out/'operation.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
