"""Scripted inputs through actual Pygame loop, on an isolated generated world."""
import argparse
import json
import os
from pathlib import Path
import tempfile
import time

os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')

import pygame
from gnome_fortress.game_session import game_session
from gnome_fortress.god_viewer import run
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_viewer import TerrainObserver


def slow_save(world,path):
    # Controlled latency creates a reproducible pending-writer navigation window.
    time.sleep(.5)
    return save_game(world,path)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    seen=[];instances=[]
    class Inspector(TerrainObserver):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw);self.frame=0;instances.append(self)
        def handle(self,events):
            self.frame+=1
            keys={1:[pygame.K_s],2:[pygame.K_a],3:[pygame.K_1],4:[pygame.K_a],
                  5:[pygame.K_F3,pygame.K_w],6:[pygame.K_t],7:[pygame.K_h],8:[pygame.K_e],10:[pygame.K_o]}
            injected=[pygame.event.Event(pygame.KEYDOWN,key=k) for k in keys.get(self.frame,[])]
            if self.frame==9:
                injected.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(5*self.tile+1,5*self.tile+1)))
            if self.frame==12:
                self.draw();pygame.image.save(self.screen,str(args.out/'pygame-saving.png'))
                seen.append(dict(kind='exit_input',tick=self.world.tick,pending=self.checkpoint_pending,watch=self.watch_id))
                injected.append(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE))
            before=self.world.rng.getstate()
            super().handle(injected)
            assert self.world.rng.getstate()==before # cast/navigation themselves draw no RNG
            seen.append(dict(frame=self.frame,tick=self.world.tick,pending=getattr(self,'checkpoint_pending',False),
                             advisor_open=self.advisor.open,tab=self.tab,watch=self.watch_id))
    with tempfile.TemporaryDirectory(prefix='saveguard-pygame-') as folder:
        path=Path(folder)/'smoke.g5.sqlite';world=TerrainWorld(1)
        with game_session(path):
            save_game(world,path)
            start=time.perf_counter()
            run(world,path,slow_save,checkpoint_ticks=300,max_frames=30,rate=60,paused=False,
                observer_class=Inspector,worker_class=TerrainCheckpointWorker)
            drained_tick=load_game(path).tick
            save_game(world,path) # launcher's normal final-state flush
            loaded=load_game(path)
            assert loaded.state()==world.state() and loaded.rng.getstate()==world.rng.getstate()
            elapsed=time.perf_counter()-start
        with game_session(path):assert load_game(path).state()==world.state()
        assert any(r.get('pending') for r in seen) and any(r.get('advisor_open') for r in seen)
        assert any(r.get('kind')=='exit_input' and r['pending'] for r in seen)
        assert len(world.interventions)==1 and world.interventions[0].kind=='rupture'
        assert world.interventions[0].status=='completed'
        result=dict(driver=os.environ.get('SDL_VIDEODRIVER'),controlled_writer_delay_seconds=.5,
            initial_saved_tick=0,drained_snapshot_tick=drained_tick,final_saved_tick=loaded.tick,
            saved_and_reloaded_exact=True,relaunch_lock_acquired=True,elapsed_seconds=elapsed,
            digest=loaded.digest(),intervention=world.interventions[0].id,
            trace=seen,human_usability_check=False)
        (args.out/'pygame-smoke.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))


if __name__=='__main__':main()
