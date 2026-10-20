"""Fast independent replay of the fixed three-tick cohort and saved evidence."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

from research.phase4b_experiment import load_probe, probe


def verify(directory):
    rows=list(csv.DictReader((directory/'probes.csv').open()))
    checks=[]
    for row in rows:
        actual,w,_=probe(int(row['seed']),row['condition'])
        assert all(str(actual[key])==value for key,value in row.items())
        checks.append(dict(seed=actual['seed'],condition=row['condition'],digest=w.digest(),exact=True))
    checkpoints=[]
    for path in sorted(directory.glob('*.sqlite')):
        w=load_probe(path)
        condition=w.protocol['condition']
        _,fresh,_=probe(1,condition)
        assert fresh.state()==w.state()
        with path.open('rb') as file:sha=hashlib.file_digest(file,'sha256').hexdigest()
        checkpoints.append(dict(path=path.name,sha256=sha,bytes=path.stat().st_size,digest=w.digest(),exact=True))
    result=dict(replays=len(checks),all_exact=all(c['exact'] for c in checks),checkpoints=checkpoints,checks=checks)
    (directory.parent/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(replays=len(checks),checkpoints=len(checkpoints),all_exact=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    verify(parser.parse_args().directory)
