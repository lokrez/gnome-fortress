"""Actual bounded Pygame controls/captures of G5–G7; natural biology only."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

import pygame
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_viewer import TerrainObserver
from gnome_fortress.terrain_storage import save_game,load_game


def capture(output):
    output.mkdir(parents=True,exist_ok=True);w=TerrainWorld(1);v=TerrainObserver(w,paused=True)
    spring=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain=='rock' and
                any(w.cell(nx,ny).terrain in ('grass','forest','hazard') for nx,ny in w.neighbors(x,y)))
    screens=[]
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    def click(pos):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)
    def inputs(*events):
        for e in events:pygame.event.post(e)
        v.handle(pygame.event.get())
    def to(tick):
        while w.tick<tick:inputs(key(pygame.K_PERIOD));v.advance(0)
    def power(name,xy):
        inputs(click(v.buttons[name].center),click((xy[0]*v.tile+v.tile//2,xy[1]*v.tile+v.tile//2)))
        assert w.interventions[-1].kind==name and w.interventions[-1].status=='queued'
    def shot(name):
        before=w.digest();v.draw();pygame.image.save(v.screen,str(output/(name+'.png')))
        assert w.digest()==before
        screens.append(dict(name=name,tick=w.tick,summary=w.summary(),digest=before,selected=v.selected,
            watch=v.watch_id,tile=v.tile_xy,tab=v.tab,advisor=v.advisor.text if v.advisor.open else None))
        for _ in range(12):pygame.event.pump();pygame.time.wait(15)
    try:
        inputs(key(pygame.K_w));shot('01-before')
        to(9);power('rupture',(2,2));to(10);inputs(key(pygame.K_o));shot('02-rupture')
        to(29);power('rewild',(2,2));to(30);inputs(key(pygame.K_o));shot('03-rewild')
        to(39);power('wellspring',spring);to(40);inputs(key(pygame.K_t),click((spring[0]*v.tile+v.tile//2,spring[1]*v.tile+v.tile//2)));shot('04-wellspring')
        inputs(click((2*v.tile+v.tile//2,2*v.tile+v.tile//2)));shot('05-tile-history')
        inputs(key(pygame.K_a),key(pygame.K_5));shot('06-advisor-land')
        inputs(key(pygame.K_1));shot('07-advisor-latest')
        before=w.state();path=output/'world.g5.sqlite';save_game(w,path);loaded=load_game(path)
        assert loaded.state()==before and v.watch_id==1
        # Real unpaused operational frames, existing pacing and recorded input only.
        inputs(key(pygame.K_a),key(pygame.K_o),key(pygame.K_SPACE))
        clock=pygame.time.Clock();frames=0
        for _ in range(120):
            seconds=clock.tick(60)/1000;inputs();v.advance(seconds);v.draw();frames+=1
        assert w.tick>40 and v.watch_id==v.selected==1
        inputs(key(pygame.K_SPACE),key(pygame.K_s));assert v.save_requested
        save_game(w,path);assert load_game(path).state()==w.state()
        inputs(key(pygame.K_ESCAPE));assert not v.running
        report=dict(driver=pygame.display.get_driver(),window=pygame.display.get_window_size(),
            input='Scripted actual queued mouse/keyboard input; no human usability session; no injected biological outcomes',
            spring_selection='First initial row-major rock adjacent to traversable terrain',spring=spring,
            screenshots=screens,interventions=[asdict(p) for p in w.interventions],
            running_frames=frames,final_tick=w.tick,final_digest=w.digest(),save_reload_exact=True)
        (output/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(driver=report['driver'],screens=len(screens),frames=frames,final_tick=w.tick)))
    finally:pygame.quit()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    capture(p.parse_args().output)
