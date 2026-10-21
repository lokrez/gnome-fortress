"""Actual isolated mature-world viewer operation with observation and autosaving."""
import json,os,pickle,tempfile,time
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.game_session import game_session
from gnome_fortress.god_viewer import run

OUT=Path('docs/g8b/evidence');CAP=Path('docs/g8b/captures')


def main():
    w=pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes())
    frames=[];captures=[];completed=[];views=[]
    class Worker(TerrainCheckpointWorker):
        def __init__(self,*args):super().__init__(*args)
        def start(self,w,path):
            t=time.perf_counter();super().start(w,path)
            captures.append(dict(tick=w.tick,ms=(time.perf_counter()-t)*1000))
        def poll(self):
            result=super().poll()
            if result:completed.append(result)
            return result
    class View(LivingObserver):
        def __init__(self,*args):
            super().__init__(*args,window_size=(1280,720));views.append(self)
            self.select_individual(min(self.world.living(),key=lambda a:(a.age,a.id)).id)
            self.action('decision-observe');self.toggle_follow();self.tested=False
            self.previous=time.perf_counter();self.frame=0
        def handle(self,events):
            now=time.perf_counter();self.frame+=1
            frames.append(dict(frame=self.frame,tick=self.world.tick,gap_ms=(now-self.previous)*1000,
                               pending=getattr(self,'checkpoint_pending',False)))
            self.previous=now;super().handle(events)
            if getattr(self,'checkpoint_pending',False) and not self.tested:
                self.tested=True
                assert self.decisions.enabled and self.follow_id==self.selected
                self.action('advisor');self.advisor.choose('1',self.world,self.selected,self.presentation)
                self.advisor.open=False;self.navigate('decisions')
                self.set_mode('rain');self.pointer=self.viewport.center
                super().handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=self.pointer)])
                self.set_mode(None);self.navigate('decisions');self.draw()
                pygame.image.save(self.screen,str(CAP/'autosave-observing.png'))
                (OUT/'autosave-observation.json').write_text(json.dumps(dict(seed=w.seed,tick=w.tick,
                    identity=self.selected,record=self.current_decision_record(),follow=self.follow_id),indent=2)+'\n')
            if completed:
                self.navigate('decisions');self.draw()
                pygame.image.save(self.screen,str(CAP/'autosave-complete.png'))
                super().handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
    with tempfile.TemporaryDirectory(prefix='g8b-operational-') as temporary:
        path=Path(temporary)/'mature.g5.sqlite'
        with game_session(path):
            save_game(w,path)
            run(w,path,save_game,checkpoint_ticks=600,max_frames=3600,rate=30,observer_class=View,worker_class=Worker)
            assert completed and views[0].tested and not getattr(views[0],'save_error',False)
            save_game(w,path);exit_tick=w.tick;loaded=load_game(path);assert loaded.state()==w.state()
            loaded.step(30);w.step(30);assert loaded.state()==w.state()
    gaps=[r['gap_ms'] for r in frames];pending=[r['gap_ms'] for r in frames if r['pending']]
    result=dict(driver=os.environ['SDL_VIDEODRIVER'],human_playtest=False,frames=frames,captures=captures,
        completions=completed,exit_saved_tick=exit_tick,continuation_exact=True,final_tick=w.tick,
        max_gap_ms=max(gaps),pending_max_gap_ms=max(pending),
        digest=w.digest(),trace_length=len(views[0].decisions.records),selected=views[0].selected,
        follow=views[0].follow_id)
    (OUT/'operation.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
