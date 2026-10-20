"""Bounded G3 compatibility and documented viewer-defect reproduction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
import types

from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game,save_game
from gnome_fortress.god_viewer import GodObserver
from gnome_fortress import god_viewer
import pygame

G2='307e511335c6102e72e45d836dd8f07550271027'
G1='597b0eb9bfcbee438c1959c6a73b1b3591511358'


def old_module(ref,path,name):
    source=subprocess.check_output(['git','show',ref+':'+path])
    m=types.ModuleType('gnome_fortress.'+name);m.__package__='gnome_fortress';m.__file__=str(Path(path).resolve())
    exec(compile(source,'<'+ref[:7]+' '+path+'>','exec'),m.__dict__)
    return m


def retry_case(module):
    calls=[];original=module.GodObserver;clock=pygame.time.Clock
    class Inspector(GodObserver):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.started=False
        def handle(self,events):
            super().handle(events)
            if not self.started:self.world.step();self.started=True
    class Clock:
        def tick(self,hz):time.sleep(.01);return 0
    def fail(world,path):calls.append(world.tick);raise OSError('controlled failure fixture')
    try:
        module.GodObserver=Inspector;pygame.time.Clock=Clock
        try:module.run(GameWorld(),Path('unused.g1.sqlite'),fail,checkpoint_ticks=1,paused=True,max_frames=8)
        except OSError:pass  # Old loop may close with another failed future pending.
    finally:module.GodObserver=original;pygame.time.Clock=clock
    return len(calls)


def verify(output):
    output.mkdir(parents=True,exist_ok=True);checks=[]
    for name in ('engine.py','model.py','game.py','game_storage.py','storage.py','runtime.py','god_demo.py','viewer.py','game_presentation.py'):
        assert Path('gnome_fortress',name).read_bytes()==subprocess.check_output(['git','show',G2+':gnome_fortress/'+name]),name
    with tempfile.TemporaryDirectory() as folder:
        for reference in (G1,G2):
            old=old_module(reference,'gnome_fortress/game_storage.py','_g3_old_storage')
            a=GameWorld(1);a.step(20);a.request('rain',24,16,8,150);a.request('drought',22,16,3,50);a.step(15)
            path=Path(folder)/(reference[:7]+'.g1.sqlite');old.save_game(a,path)
            raw=path.read_bytes();b=load_game(path)
            assert b.state()==a.state() and raw==path.read_bytes()
            v=GodObserver(b,paused=True)
            try:
                v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_F3),pygame.event.Event(pygame.KEYDOWN,key=pygame.K_w)])
                v.draw();before=b.state();save_game(b,Path(folder)/'roundtrip.g1.sqlite')
                assert v.watch_id==v.selected==1 and b.state()==before
                assert old.load_game(Path(folder)/'roundtrip.g1.sqlite').state()==b.state()
            finally:pygame.quit()
            a.step(90);b.step(90);assert a.state()==b.state()
            checks.append(dict(producer=reference,active_save_exact=True,old_reader_accepts_save=True,continuation_digest=b.digest()))
        fixture=Path(folder)/'fixture.g1.sqlite'
        fixture.write_bytes(gzip.decompress(Path('docs/g2/verification/legacy-active.g1.gz').read_bytes()))
        raw=fixture.read_bytes();w=load_game(fixture)
        assert w.digest()==json.loads(Path('docs/g2/verification/legacy-active.json').read_text())['digest']
        assert fixture.read_bytes()==raw
        checks.append(dict(fixture='G2 retained G1-writer fixture',exact=True))
    data=json.loads(Path('docs/g1/results/comparison.json').read_text())
    for condition,row in data['final'].items():
        w=GameWorld(1);w.step(20)
        if condition!='observation':w.request(condition,24,16,8,150)
        w.step(280);assert w.digest()==row['digest']
        checks.append(dict(recorded_G1_outcome=condition,exact=True,digest=w.digest()))
    old_view=old_module(G2,'gnome_fortress/god_viewer.py','_g3_old_viewer')
    before,after=retry_case(old_view),retry_case(god_viewer)
    assert before>1 and after==1
    report=dict(reference=G2,checks=checks,unchanged_authoritative_modules=9,
        save_format='gnome-fortress-game-g1-v1',retry_fixture=dict(frames=8,G2_attempts=before,G3_attempts=after),
        scope='bounded verification; synthetic disk failure, no endurance campaign')
    (output/'compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


def replay_smoke(path,output):
    recorded=json.loads(path.read_text());world=GameWorld(1)
    for p in recorded['interventions']:
        world.step(p['requested_tick']-world.tick)
        created=world.request(p['kind'],p['x'],p['y'],p['radius'],p['duration'])
        assert created.id==p['id']
    world.step(recorded['summary']['tick']-world.tick)
    assert world.digest()==recorded['digest']
    with tempfile.TemporaryDirectory() as folder:
        checkpoint=Path(folder)/'smoke.g1.sqlite';save_game(world,checkpoint);loaded=load_game(checkpoint)
        world.step(20);loaded.step(20);assert world.state()==loaded.state()
    output.mkdir(parents=True,exist_ok=True)
    report=dict(seed=1,replayed_ticks=recorded['summary']['tick'],exact_recorded_UI_digest=recorded['digest'],
                active_input_sequence_exact=True,save_reload_continuation_ticks=20,continuation_exact=True)
    (output/'smoke-replay.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--smoke-report',type=Path)
    args=p.parse_args()
    if args.smoke_report:replay_smoke(args.smoke_report,args.output)
    else:verify(args.output)
