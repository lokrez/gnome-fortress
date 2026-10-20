"""Actual Pygame captures of naturally simulated individuals and family navigation."""
import argparse
import json
from pathlib import Path

from gnome_fortress.game import GameWorld
from gnome_fortress.life_presentation import life_summary,life_event_text
from gnome_fortress.god_viewer import GodObserver
import pygame


def capture(output):
    output.mkdir(parents=True,exist_ok=True);w=GameWorld(1);v=GodObserver(w,paused=True);shots=[]
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    def step_to(tick):
        while w.tick<tick:v.handle([key(pygame.K_PERIOD)]);v.advance(0)
    def shot(name):
        before=w.digest();v.draw();pygame.image.save(v.screen,str(output/(name+'.png')))
        assert w.digest()==before
        start=max(0,len(v.life.positions)-v.life_capacity) if v.life_tail else v.life_start
        shots.append(dict(name=name,tick=w.tick,selected=v.selected,watch_id=v.watch_id,
            individual=life_summary(w,v.selected),family=v.life.family(v.family_start,v.family_capacity),
            timeline=[dict(sequence=i,tick=e.tick,text=life_event_text(e,v.selected)) for i,e in v.life.page(start,v.life_capacity)],
            digest=before))
        pygame.event.pump()
    try:
        v.select_individual(53);v.handle([key(pygame.K_F3),key(pygame.K_w)]);shot('quiet-founder')
        step_to(20)
        for power,x in ((pygame.K_r,20),(pygame.K_d,22)):
            pos=(x*v.tile+v.tile//2,16*v.tile+v.tile//2)
            v.handle([key(power),pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos),key(pygame.K_o),key(pygame.K_F3)])
        step_to(120);shot('watched-founder')
        # Choose a real parent; biological events are never injected for this capture.
        parent=min(a.id for a in w.agents.values() if a.children>0)
        v.select_individual(parent);v.life_pane='family';v.draw();shot('family')
        child=v.life.family(0,1)['children'][0]['id']
        row=next(rect for rect,identity in v.family_hits if identity==child)
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=row.center)])
        v.life_pane='events';v.handle([key(pygame.K_w)]);shot('descendant')
        report=dict(driver=pygame.display.get_driver(),window=pygame.display.get_window_size(),
                    input='scripted actual controls; natural seed-1 biology; no forced births, deaths, relationships or life events',screens=shots)
        (output/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(driver=report['driver'],window=report['window'],captures=len(shots))))
    finally:pygame.quit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
