"""Bounded real-time UI smoke; actual simulation, no forced life events."""
import argparse
import json
from pathlib import Path
import tempfile
import time

from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import save_game,load_game
from gnome_fortress import god_viewer
from gnome_fortress.life_presentation import life_summary
import pygame


def run(output,seconds=180):
    output.mkdir(parents=True,exist_ok=True)
    w=GameWorld(1);original=god_viewer.GodObserver;instances=[];began=time.monotonic()
    class Witness(original):
        def __init__(self,*args,**kw):
            super().__init__(*args,**kw);self.started=False;self.actions=set();self.frames_seen=0
            self.anchor=None;self.anchor_verified=False;instances.append(self)
        def handle(self,events):
            super().handle(events);self.frames_seen+=1
            def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
            if not self.started:
                super().handle([key(pygame.K_F3),key(pygame.K_w)]);self.started=True
            assert self.watch_id==self.selected==1
            if not self.saving:
                for tick,power,x in ((20,pygame.K_r,20),(120,pygame.K_d,22)):
                    if w.tick>=tick and tick not in self.actions:
                        pos=(x*self.tile+self.tile//2,16*self.tile+self.tile//2)
                        super().handle([key(power),pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos),key(pygame.K_o),key(pygame.K_F3)])
                        self.actions.add(tick)
                if w.tick>=100 and 'save' not in self.actions:
                    super().handle([key(pygame.K_s)]);self.actions.add('save')
            if w.tick>=600 and self.anchor is None:
                self.browse_life(-self.life_capacity)
                self.anchor=(self.life_start,[i for i,_ in self.life.page(self.life_start,self.life_capacity)])
            if w.tick>=900 and self.anchor and not self.anchor_verified:
                assert self.life_start==self.anchor[0]
                assert [i for i,_ in self.life.page(self.life_start,self.life_capacity)]==self.anchor[1]
                self.anchor_verified=True;self.life_tail=True
    try:
        god_viewer.GodObserver=Witness
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'watch.g1.sqlite'
            god_viewer.run(w,path,save_game,checkpoint_ticks=300,stop_requested=lambda:time.monotonic()-began>=seconds,
                           rate=15,capture=output/'witness.png')
            save_game(w,path);loaded=load_game(path)
            assert loaded.state()==w.state()
            v=instances[0]
            report=dict(wall_seconds=time.monotonic()-began,driver='actual SDL display; see capture metadata',
                frames=v.frames_seen,summary=w.summary(),selected=v.selected,watch_id=v.watch_id,
                individual=life_summary(w,1),scroll_anchor_verified=v.anchor_verified,
                save_reload_exact=True,interventions=w.state()['game']['interventions'],digest=w.digest(),
                input='scripted documented controls; no human usability claim; no forced biological events')
            (output/'watch-smoke.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(report,indent=2))
    finally:god_viewer.GodObserver=original


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seconds',type=float,default=180);args=p.parse_args();run(args.output,args.seconds)
