"""Replay every declared controlled branch and ordinary-world pilot."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import time

from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld
from research.phase4c_matrix import MatrixWorld, attenuate
from research.phase4c_pilot import run_world
from research.phase4c_study import ablation, encode


def verify(directory):
    started=time.perf_counter();counts={}
    with (directory/'ablations.csv').open() as f:
        saved=list(csv.DictReader(f))
    replay=[encode(row) for seed in range(1,65) for row in ablation(seed)]
    assert saved==replay,'Original-seed ablation mismatch'
    counts['ablation_rows']=len(replay)
    count=0;key=None;world=None
    with gzip.open(directory/'matrix.csv.gz','rt',newline='') as f:
        for saved in csv.DictReader(f):
            new_key=int(saved['seed']),int(saved['depth'])
            if new_key!=key:world=MatrixWorld(*new_key);key=new_key
            actual=world.case(int(saved['source']),int(saved['margin']),saved['rounding'],saved['condition'])
            assert saved==encode(actual),f'Matrix mismatch {count}: {new_key}'
            count+=1
    counts['matrix_rows']=count
    with (directory/'arithmetic.csv').open() as f:
        arithmetic=list(csv.DictReader(f))
    current=None;value=0
    for row in arithmetic:
        key=row['rounding'],int(row['source'])
        if key!=current:value=key[1];current=key
        packet,value=attenuate(value,key[0])
        assert int(row['packet'])==packet and int(row['acquired'])==value
    counts['arithmetic_rows']=len(arithmetic)
    pilots=json.loads((directory/'pilot.json').read_text())
    for saved in pilots:
        actual,world,_=run_world(saved['seed'],saved['condition'],saved['ticks'])
        # JSON normalizes tuples to lists.
        assert json.loads(json.dumps(actual))==saved,'Pilot metric replay mismatch'
        reference=TelephoneWorld(saved['seed'],TelephoneConfig(saved['condition']))
        reference.step(saved['ticks'])
        assert reference.state()==world.state(),'Passive observation changed the world'
    counts['pilot_replays']=len(pilots);counts['uninstrumented_world_comparisons']=len(pilots)
    counts['seconds']=time.perf_counter()-started
    (directory/'verification.json').write_text(json.dumps(counts,indent=2)+'\n')
    print(json.dumps(counts,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
