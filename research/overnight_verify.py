"""Preservation, legacy reader/import and exact default-viewer equivalence checks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import pygame
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game as load_legacy
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import import_legacy,load_game,save_game
from gnome_fortress.god_viewer import GodObserver
from gnome_fortress.engine import World
from research.g3_verify import old_module

BASE='0508849cea815f325e87973a06e810ad2e8c41ec'
REFERENCES=['597b0eb9bfcbee438c1959c6a73b1b3591511358','307e511335c6102e72e45d836dd8f07550271027',
            '40eeac5cb8893f02d32e456b4a778badf3cc998f',BASE]


def viewer_trial(cls):
    w=GameWorld(2);v=cls(w,paused=True)
    def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
    try:
        for k in (pygame.K_w,pygame.K_r):v.handle([key(k)])
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(50,70)),key(pygame.K_o)])
        for _ in range(20):v.handle([key(pygame.K_PERIOD)]);v.advance(0)
        v.handle([key(pygame.K_F3)]);v.draw()
        pixels=hashlib.sha256(pygame.image.tobytes(v.screen,'RGB')).hexdigest()
        v.handle([key(pygame.K_a),key(pygame.K_3),key(pygame.K_2)]);v.draw()
        dialogue=hashlib.sha256(pygame.image.tobytes(v.screen,'RGB')).hexdigest()
        return dict(state=w.digest(),selected=v.selected,watch=v.watch_id,pixels=pixels,dialogue_pixels=dialogue)
    finally:pygame.quit()


def verify(output):
    output.mkdir(parents=True,exist_ok=True);legacy=[]
    with tempfile.TemporaryDirectory() as folder:
        for ref in REFERENCES:
            old=old_module(ref,'gnome_fortress/game_storage.py','_overnight_old_storage')
            a=GameWorld(2);a.step(9);a.request('rain',1,1);a.request('drought',2,2,2,45);a.step(11)
            src=Path(folder)/(ref[:7]+'.g1.sqlite');dst=Path(folder)/(ref[:7]+'.g5.sqlite')
            old.save_game(a,src);raw=src.read_bytes();b=import_legacy(src,dst)
            assert old.load_game(src).state()==a.state() and load_legacy(src).state()==a.state()
            assert World.state(a)==World.state(b) and src.read_bytes()==raw
            a.step(90);b.step(90);assert World.state(a)==World.state(b)
            save_game(b,dst);assert load_game(dst).state()==b.state()
            legacy.append(dict(reference=ref,source_bytes_unchanged=True,original_reader=True,import_exact=True,continuation_ticks=90,continuation_exact=True))
        fixture=Path('docs/g2/verification/legacy-active.g1.gz')
        src=Path(folder)/'archived.g1.sqlite';src.write_bytes(gzip.decompress(fixture.read_bytes()));raw=src.read_bytes()
        old=load_legacy(src);new=import_legacy(src,Path(folder)/'archived.g5.sqlite')
        old.step(30);new.step(30);assert World.state(old)==World.state(new) and src.read_bytes()==raw
    old_viewer=old_module(BASE,'gnome_fortress/god_viewer.py','_overnight_g4_viewer')
    reference=viewer_trial(old_viewer.GodObserver);current=viewer_trial(GodObserver)
    assert reference==current
    allowed={'README.md','gnome_fortress/god_viewer.py'};preserved=[];normalized=[]
    for path in subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],text=True).splitlines():
        if path in allowed:continue
        raw=Path(path).read_bytes();old=subprocess.check_output(['git','show',BASE+':'+path])
        if raw!=old:
            assert path.endswith('.csv') and raw.replace(b'\r\n',b'\n')==old,path
            normalized.append(path)
        preserved.append(path)
    tags=subprocess.check_output(['git','show-ref','--tags'],text=True).splitlines()
    assert tags==json.loads(Path('docs/g4/evidence/verification.json').read_text())['tags']
    unchanged=[]
    for name in ('engine.py','model.py','game.py','game_storage.py','storage.py','runtime.py','god_demo.py','viewer.py','game_presentation.py','life_presentation.py','advisor.py'):
        path='gnome_fortress/'+name
        assert Path(path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path]);unchanged.append(path)
    report=dict(accepted_baseline=BASE,legacy=legacy,archived_g1_fixture_import_continuation_exact=True,
        default_viewer_exact=reference,preserved_files=len(preserved),preserved_research_files=sum(p.startswith('research/') for p in preserved),
        allowed_existing_changes=sorted(allowed),existing_csv_normalization=normalized,tags_exact=True,tags=tags,
        authoritative_and_legacy_modules_unchanged=unchanged,
        source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('gnome_fortress').glob('*.py'))})
    (output/'preservation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(legacy=len(legacy),preserved=len(preserved),tags_exact=True,default_viewer_pixels_and_state_exact=True)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    verify(p.parse_args().output)
