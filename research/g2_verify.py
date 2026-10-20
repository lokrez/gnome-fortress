"""Bounded G1 compatibility check, using source read from the accepted Git commit."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import types

from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game,save_game

G1='597b0eb9bfcbee438c1959c6a73b1b3591511358'


def old_module(path,name):
    source=subprocess.check_output(['git','show',G1+':'+path])
    module=types.ModuleType('gnome_fortress.'+name);module.__package__='gnome_fortress';module.__file__=str(Path(path).resolve())
    # Game and engine are deliberately byte-identical; the old writer is executed.
    exec(compile(source,'<G1 '+path+'>','exec'),module.__dict__)
    return module,hashlib.sha256(source).hexdigest()


def verify(output):
    output.mkdir(parents=True,exist_ok=True)
    for name in ('engine.py','game.py','game_storage.py','storage.py','runtime.py','god_demo.py','viewer.py'):
        assert Path('gnome_fortress',name).read_bytes()==subprocess.check_output(['git','show',G1+':gnome_fortress/'+name]),name
    legacy,source_hash=old_module('gnome_fortress/game_storage.py','_g2_legacy_storage')
    results=[]
    with tempfile.TemporaryDirectory() as folder:
        for scenario,ticks in (('queued',0),('active',14),('expired',45),('extinct',0)):
            original=GameWorld(1);original.step(9)
            original.request('rain',1,1,5,25);original.request('drought',2,2,2,11)
            original.step(ticks)
            if scenario=='extinct':
                for a in list(original.living()):original.kill(a,'verification_fixture')
            path=Path(folder)/(scenario+'.g1.sqlite')
            legacy.save_game(original,path)
            raw=path.read_bytes();loaded=load_game(path)
            assert raw==path.read_bytes() and loaded.state()==original.state()
            if scenario=='active':
                (output/'legacy-active.g1.gz').write_bytes(gzip.compress(raw,mtime=0))
                (output/'legacy-active.json').write_text(json.dumps(dict(producer_commit=G1,
                    writer_sha256=source_hash,checkpoint_sha256=hashlib.sha256(raw).hexdigest(),
                    digest=original.digest(),tick=original.tick),indent=2)+'\n')
            roundtrip=Path(folder)/(scenario+'-roundtrip.g1.sqlite')
            save_game(loaded,roundtrip)
            assert legacy.load_game(roundtrip).state()==loaded.state()
            original.step(90);loaded.step(90)
            assert loaded.state()==original.state()
            results.append(dict(scenario=scenario,exact=True,g1_reader_accepts_g2_save=True,final_tick=loaded.tick,digest=loaded.digest()))
        for seed in (1,42):
            a,b=GameWorld(seed),GameWorld(seed)
            for w in (a,b):
                w.step(20);w.request('rain',24,16,8,150);w.request('drought',24,16,3,50);w.step(280)
            assert a.state()==b.state()
            results.append(dict(scenario='matched_interventions',seed=seed,exact=True,digest=a.digest()))
    # Original G1 dataset is an independent fixed outcome check, not a new study.
    expected=json.loads(Path('docs/g1/results/comparison.json').read_text())
    for condition,saved in expected['final'].items():
        w=GameWorld(1);w.step(20)
        if condition!='observation':w.request(condition,24,16,8,150)
        w.step(280)
        assert w.digest()==saved['digest'],condition
        results.append(dict(scenario='G1_recorded_'+condition,exact=True,digest=w.digest()))
    original_path=Path('run-results/god/g1-smoke.g1.sqlite')
    if original_path.exists():
        raw=original_path.read_bytes();original=load_game(original_path)
        expected_smoke=json.loads(Path('docs/g1/launcher-smoke.txt').read_text())
        assert original.digest()==expected_smoke['digest'] and raw==original_path.read_bytes()
        results.append(dict(scenario='existing_G1_smoke_readonly',exact=True,digest=original.digest(),
                            file_sha256=hashlib.sha256(raw).hexdigest()))
    report=dict(reference=G1,unchanged_authoritative_modules=7,checks=results,
                format='gnome-fortress-game-g1-v1',new_format_or_modes=False)
    (output/'compatibility.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
