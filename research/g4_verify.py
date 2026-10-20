"""Bounded G4 scripted Pygame operational check and legacy compatibility."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

import pygame
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game,save_game
from gnome_fortress.god_viewer import GodObserver
from research.g3_verify import old_module

BASE='40eeac5cb8893f02d32e456b4a778badf3cc998f'


def verify(output):
    output.mkdir(parents=True,exist_ok=True)
    unchanged=[]
    for name in ('engine.py','model.py','game.py','game_storage.py','storage.py','runtime.py','god_demo.py','viewer.py','game_presentation.py','life_presentation.py'):
        path='gnome_fortress/'+name
        assert Path(path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path])
        unchanged.append(path)
    compatibility=[]
    with tempfile.TemporaryDirectory() as folder:
        for ref in ('597b0eb9bfcbee438c1959c6a73b1b3591511358','307e511335c6102e72e45d836dd8f07550271027',BASE):
            old=old_module(ref,'gnome_fortress/game_storage.py','_g4_old_storage')
            a=GameWorld(1);a.step(20);a.request('rain',20,16);a.request('drought',22,16,3,30);a.step(15)
            path=Path(folder)/'legacy.g1.sqlite';old.save_game(a,path);raw=path.read_bytes();b=load_game(path)
            assert a.state()==b.state() and path.read_bytes()==raw
            v=GodObserver(b,paused=True)
            try:
                for topic in (pygame.K_1,pygame.K_2,pygame.K_3,pygame.K_4):
                    v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_a),pygame.event.Event(pygame.KEYDOWN,key=topic)])
                    v.draw();v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_a)])
                assert a.state()==b.state()
                roundtrip=Path(folder)/'roundtrip.g1.sqlite';save_game(b,roundtrip)
                assert old.load_game(roundtrip).state()==a.state()
                a.step(90);b.step(90);assert a.state()==b.state()
                compatibility.append(dict(reference=ref,readonly_source=True,roundtrip=True,continuation_ticks=90,exact=True))
            finally:pygame.quit()
    # Natural seed-1 biology. UI requests only; no forced deaths or events.
    w=GameWorld(1);v=GodObserver(w,paused=True);v.select_individual(53);v.watch_id=53
    screens=[];started=time.perf_counter()
    def inputs(*events):
        for e in events:pygame.event.post(e)
        v.handle(pygame.event.get())
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    def click(pos):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)
    def shot(name):
        before=w.digest();v.draw();pygame.image.save(v.screen,str(output/(name+'.png')))
        assert w.digest()==before
        screens.append(dict(name=name,tick=w.tick,text=v.advisor.text,page=v.advisor.page,selected=v.selected,watch=v.watch_id,digest=before))
        for _ in range(15):pygame.event.pump();pygame.time.wait(15)
    try:
        inputs(click(v.advisor_button.center));shot('advisor-main')
        inputs(key(pygame.K_1));shot('advisor-world');inputs(key(pygame.K_0),key(pygame.K_a))
        w.step(20)
        for power,x in ((pygame.K_r,20),(pygame.K_d,22)):
            inputs(key(power),click((x*v.tile+v.tile//2,16*v.tile+v.tile//2)),key(pygame.K_o))
        w.step(100)
        inputs(key(pygame.K_a),key(pygame.K_2));shot('advisor-gnome')
        assert not w.agents[53].alive and v.watch_id==53
        inputs(key(pygame.K_0),key(pygame.K_3),key(pygame.K_2));shot('advisor-powers')
        # Mouse navigation must open real ledger, then return to Watch's Life view.
        rect=next(r for r,c in v.advisor_hits if c=='1');inputs(click(rect.center))
        assert v.tab=='powers' and not v.advisor.open and v.watch_id==53
        inputs(key(pygame.K_F3));v.draw();assert v.selected==v.watch_id==53
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'operational.g1.sqlite';save_game(w,path);assert load_game(path).state()==w.state()
        inputs(key(pygame.K_a),key(pygame.K_4),key(pygame.K_3));shot('advisor-complaint')
        inputs(key(pygame.K_ESCAPE));assert not v.running
        report=dict(baseline=BASE,driver=pygame.display.get_driver(),window=pygame.display.get_window_size(),
            input='scripted actual Pygame key/mouse event queue; natural seed-1 biology; no human usability session',
            seconds=time.perf_counter()-started,compatibility=compatibility,unchanged_modules=unchanged,screens=screens)
    finally:pygame.quit()
    # All pre-existing tracked files except the two intended presentation/docs edits.
    preserved=[]
    for path in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],text=True).splitlines():
        if path in ('README.md','gnome_fortress/god_viewer.py'):continue
        old=subprocess.check_output(['git','show',BASE+':'+path])
        raw=Path(path).read_bytes()
        assert raw==old or (path.endswith('.csv') and raw.replace(b'\r\n',b'\n')==old),path
        preserved.append(path)
    report['preserved_historical_files']=len(preserved)
    report['tags']=subprocess.check_output(['git','show-ref','--tags'],text=True).splitlines()
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(compatibility=len(compatibility),preserved=len(preserved),driver=report['driver'],screens=len(screens))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
