"""Scripted input to the actual running G2 build; no human usability claim."""
import argparse
import json
from pathlib import Path

from gnome_fortress.game import GameWorld
from gnome_fortress.game_presentation import agent_view,event_text
from gnome_fortress.god_viewer import GodObserver
import pygame


def capture(output):
    output.mkdir(parents=True,exist_ok=True)
    w=GameWorld(1);v=GodObserver(w,paused=True);clock=pygame.time.Clock()
    evidence=[]
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    def step_to(tick):
        while w.tick<tick:
            v.handle([key(pygame.K_PERIOD)]);v.advance(0)
    def shot(name):
        before=w.digest();v.draw()
        pygame.image.save(v.screen,str(output/(name+'.png')))
        assert before==w.digest()
        evidence.append(dict(name=name,tick=w.tick,tab=v.tab,selected=agent_view(w,v.selected),
            status=dict(v.presentation.status),powers=v.presentation.powers,
            feed=[dict(sequence=i,tick=e.tick,text=event_text(e,w)) for i,e in v.presentation.events.page(v.event_offset,v.event_capacity)],
            digest=before))
        pygame.event.pump();clock.tick(30)
    try:
        shot('founders')
        step_to(20)
        for power,x in ((pygame.K_r,20),(pygame.K_r,20),(pygame.K_d,22)):
            pos=(x*v.tile+v.tile//2,16*v.tile+v.tile//2)
            v.handle([key(power),pygame.event.Event(pygame.MOUSEMOTION,pos=pos),
                pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)])
        v.handle([key(pygame.K_o)]);step_to(120);shot('powers-active')
        # Choose a genuinely living descendant, preferring a naturally sleeping one.
        candidates=[a for a in w.living() if a.parents]
        a=min(candidates,key=lambda a:(not(a.sleep_until>w.tick),a.id))
        v.selected=a.id;v.handle([key(pygame.K_F1)]);shot('individual')
        v.handle([key(pygame.K_PAGEUP)]);shot('events-browsed')
        v.handle([key(pygame.K_END),key(pygame.K_F2)]);step_to(221);shot('powers-expired')
        report=dict(driver=pygame.display.get_driver(),window=pygame.display.get_window_size(),
            input='scripted actual key/click handlers; no human usability session',screens=evidence)
        (output/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(driver=report['driver'],window=report['window'],captures=len(evidence))))
    finally:pygame.quit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
