"""Predeclared Phase 4C cohorts. No long experiment is available through this CLI."""
import argparse
from collections import defaultdict
import csv
import gzip
import io
import hashlib
import json
from pathlib import Path
import time

from research.phase4b_experiment import ThreeGnomesWorld
from research.phase4c_tools import digest,execute
from research.phase4c_matrix import (CONDITIONS,DEPTHS,MARGINS,MODES,SEEDS,STRENGTHS,MatrixWorld,attenuate)
from research.phase4c_pilot import run_world,SEEDS as PILOT_SEEDS,CONDITIONS as PILOT_CONDITIONS,TICKS


def encode(row):
    return {k:json.dumps(v,sort_keys=True,separators=(',',':')) if isinstance(v,(dict,list,tuple)) else str(v) for k,v in row.items()}


def ablation(seed):
    initial=ThreeGnomesWorld(seed);initial.step(2)
    data=initial.state();rows=[]
    for ablate in (False,True):
        world=ThreeGnomesWorld.from_state(data);a=world.agents[3]
        r=execute(world,a,lambda:world.step(),ablate=ablate,full_boundary=True)
        r.update(seed=seed,condition='ablated' if ablate else 'original',post_digest=world.digest())
        rows.append(r)
    assert rows[0]['full_boundary']==rows[1]['full_boundary']
    assert rows[0]['rng_before']==rows[1]['rng_before']
    return rows


def write_csv(path,rows):
    rows=iter(rows);first=next(rows)
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(first),lineterminator='\n')
        writer.writeheader();writer.writerow(encode(first))
        for row in rows:writer.writerow(encode(row))


def run(output):
    if output.exists():raise ValueError('Preserving results: use a new output directory')
    output.mkdir(parents=True)
    started=time.perf_counter()
    ablations=[row for seed in range(1,65) for row in ablation(seed)]
    write_csv(output/'ablations.csv',ablations)
    altered=[];avoided=[];unchanged=[];matched=[]
    for before,after in zip(ablations[::2],ablations[1::2]):
        seed=before['seed']
        if before['chosen'][1:]!=after['chosen'][1:]:altered.append(seed)
        else:unchanged.append(seed)
        if after['terrain']=='hazard' and before['terrain']!='hazard':avoided.append(seed)
        changed=before['chosen'][1:]!=after['chosen'][1:]
        reason=('hazard_avoided' if after['terrain']=='hazard' and before['terrain']!='hazard'
                else 'safe_tie_remapping' if changed else 'already_safe_same_choice')
        matched.append(dict(seed=seed,acquired=before['stored_hazard'],firsthand_before=before['firsthand_before'],
            original_scores=before['scores'],ablated_scores=after['scores'],original_chosen=before['chosen'],
            ablated_chosen=after['chosen'],decision_changed=changed,reason=reason,
            rng_before=before['rng_before'],full_boundary=before['full_boundary']))
    write_csv(output/'matched-seeds.csv',matched)
    arithmetic=[]
    for mode in MODES:
        for source in range(-100,101):
            value=source
            for depth in range(1,8):
                packet,value=attenuate(value,mode)
                arithmetic.append(dict(rounding=mode,source=source,depth=depth,packet=packet,acquired=value))
    write_csv(output/'arithmetic.csv',arithmetic)
    aggregates=defaultdict(lambda:defaultdict(int));cases=0
    with (output/'matrix.csv.gz').open('wb') as raw:
        with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
            with io.TextIOWrapper(compressed,newline='') as file:
                writer=None
                for seed in SEEDS:
                    for depth in DEPTHS:
                        template=MatrixWorld(seed,depth)
                        for mode in MODES:
                            for strength in STRENGTHS:
                                for margin in MARGINS:
                                    rngs=set();bodies=set()
                                    for condition in CONDITIONS:
                                        row=template.case(strength,margin,mode,condition)
                                        rngs.add(row['rng_before']);bodies.add(row['unrelated_before'])
                                        if writer is None:
                                            writer=csv.DictWriter(file,fieldnames=list(row),lineterminator='\n');writer.writeheader()
                                        writer.writerow(encode(row));cases+=1
                                        group=aggregates[(mode,strength,depth,margin,condition)]
                                        for name in ('target_delivered','score_applicable','hazard_warning_applied','ranking_changed','baseline_hazard','hazard_avoided','hazard_increased','decision_changed'):
                                            group[name]+=int(row[name])
                                        group['trials']+=1
                                        group['acquired_sum']+=row['acquired_hazard']
                                    assert len(rngs)==len(bodies)==1
    write_csv(output/'matrix-aggregate.csv',(dict(rounding=k[0],source=k[1],depth=k[2],margin=k[3],condition=k[4],**v) for k,v in sorted(aggregates.items())))
    pilots=[];timings=[]
    for seed in PILOT_SEEDS:
        for condition in PILOT_CONDITIONS:
            metrics,world,seconds=run_world(seed,condition)
            pilots.append(metrics);timings.append(dict(seed=seed,condition=condition,seconds=seconds))
    (output/'pilot.json').write_text(json.dumps(pilots,indent=2)+'\n')
    (output/'timings.json').write_text(json.dumps(dict(pilot=timings,total_seconds=time.perf_counter()-started),indent=2)+'\n')
    summary=dict(protocol_sha256=hashlib.sha256(Path('research/phase4c/PROTOCOL.md').read_bytes()).hexdigest(),
        original_seeds=64,ablation_decision_changed=altered,ablation_hazard_avoided=avoided,
        ablation_same_position=unchanged,matrix_rows=cases,pilot_worlds=len(pilots),pilot_ticks=TICKS)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
