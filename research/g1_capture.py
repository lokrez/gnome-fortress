"""Capture the actual running SDL/Pygame build using documented UI controls."""
import argparse
import json
from pathlib import Path
import time

from gnome_fortress.game import GameWorld
from gnome_fortress.god_viewer import GodObserver
import pygame


def capture(output):
    output.mkdir(parents=True,exist_ok=True)
    w=GameWorld(1);v=GodObserver(w,paused=True);clock=pygame.time.Clock()
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    try:
        v.draw();pygame.image.save(v.screen,str(output/'founders.png'))
        for _ in range(20):
            v.handle([key(pygame.K_PERIOD)]);v.advance(0)
        v.draw();pygame.image.save(v.screen,str(output/'before.png'))
        # Exercise exactly the power-selection/map-target controls players use.
        for kind,x in ((pygame.K_r,20),(pygame.K_d,28)):
            pos=(x*v.tile+v.tile//2,16*v.tile+v.tile//2)
            v.handle([key(kind),pygame.event.Event(pygame.MOUSEMOTION,pos=pos),
                      pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)])
        for _ in range(10):
            pygame.event.pump();v.handle([key(pygame.K_PERIOD)]);v.advance(0);v.draw();clock.tick(30)
        v.draw();pygame.image.save(v.screen,str(output/'active.png'))
        metadata=dict(driver=pygame.display.get_driver(),display=pygame.display.get_window_size(),
                      tick=w.tick,summary=w.summary(),interventions=w.state()['game']['interventions'],
                      input='scripted documented Pygame key and click events; not human manual QA',digest=w.digest())
        (output/'capture.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(json.dumps(metadata,indent=2))
    finally:pygame.quit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
