"""Derive tables and an optional static research figure from immutable primary rows."""
import argparse
from collections import defaultdict
import csv
import gzip
import json
from pathlib import Path
from statistics import mean

from research.phase4c_matrix import DEPTHS, MARGINS, STRENGTHS
from research.phase4c_study import write_csv

FIELDS=('target_delivered','score_applicable','ranking_changed','baseline_hazard','hazard_avoided','hazard_increased','decision_changed')


def analyze(directory,plot=False):
    with gzip.open(directory/'matrix.csv.gz','rt',newline='') as file:
        rows=list(csv.DictReader(file))
    groups=defaultdict(lambda:defaultdict(int));margins=defaultdict(lambda:defaultdict(int))
    for r in rows:
        group=groups[r['rounding'],r['condition']];group['trials']+=1
        for field in FIELDS:group[field]+=r[field]=='True'
        if r['condition']=='multihop' and r['rounding']=='floor' and int(r['source'])<0:
            group=margins[int(r['margin'])];group['trials']+=1
            for field in FIELDS:group[field]+=r[field]=='True'
    write_csv(directory/'conditions.csv',(dict(rounding=k[0],condition=k[1],**v) for k,v in sorted(groups.items())))
    write_csv(directory/'margins.csv',(dict(margin=k,**v) for k,v in sorted(margins.items())))
    indexed={tuple(r[k] for k in ('seed','source','depth','margin','condition','rounding')):r for r in rows}
    differences=[]
    for r in rows:
        if r['rounding']!='floor' or r['condition']!='multihop':continue
        for mode in ('truncate','symmetric'):
            other=indexed[tuple(r[k] for k in ('seed','source','depth','margin','condition'))+(mode,)]
            assert r['rng_before']==other['rng_before'] and r['unrelated_before']==other['unrelated_before']
            differences.append(dict(seed=r['seed'],source=r['source'],depth=r['depth'],margin=r['margin'],alternative=mode,
                floor_score=r['acquired_hazard'],alternative_score=other['acquired_hazard'],
                changed_position=(r['chosen_x'],r['chosen_y'])!=(other['chosen_x'],other['chosen_y']),
                changed_terrain=r['chosen_terrain']!=other['chosen_terrain']))
    write_csv(directory/'arithmetic-comparisons.csv',differences)
    pilots=json.loads((directory/'pilot.json').read_text());summary=[]
    for condition in ('individual','direct','multihop','masked'):
        pp=[p for p in pilots if p['condition']==condition]
        result=dict(condition=condition,worlds=len(pp),ticks_per_world=300)
        for field in ('attempts','opportunities','messages','content_recipients','unused_no_applicable',
                      'not_personally_verified','episode_evicted','association_missing','mixed_recipients'):
            result[field]=sum(p[field] for p in pp)
        for field in ('direct_deliveries','multihop_deliveries','opaque_deliveries','clean_social_moves','applicable_moves',
                      'ranking_changed','decision_changed','hazard_avoided','mixed_excluded_moves'):
            result[field]=sum(p['counts'].get(field,0) for p in pp)
        forwarded=[r for p in pp for r in p['recipients'] if r['depth']>1 and not r['masked']]
        result.update(forwarded_recipients=len(forwarded),forwarded_applicable=sum(r['applicable_moves'] for r in forwarded),
                      forwarded_changed=sum(r['decision_changed'] for r in forwarded),forwarded_avoided=sum(r['hazard_avoided'] for r in forwarded))
        summary.append(result)
    write_csv(directory/'pilot-summary.csv',summary)
    if plot:heatmap(directory,rows)
    print(json.dumps(dict(matrix_rows=len(rows),condition_groups=len(groups),arithmetic_comparisons=len(differences))))


def heatmap(directory,rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    fig,axes=plt.subplots(2,2,figsize=(13,8),layout='constrained')
    for ax,depth in zip(axes.flat,DEPTHS):
        image=np.full((len(STRENGTHS),len(MARGINS)),np.nan)
        for i,source in enumerate(STRENGTHS):
            for j,margin in enumerate(MARGINS):
                rr=[r for r in rows if r['rounding']=='floor' and r['condition']=='multihop'
                    and int(r['depth'])==depth and int(r['source'])==source and int(r['margin'])==margin]
                denominator=sum(r['baseline_hazard']=='True' for r in rr)
                numerator=sum(r['hazard_avoided']=='True' for r in rr)
                if denominator:image[i,j]=numerator/denominator
                ax.text(j,i,f'{numerator}/{denominator}' if denominator else '—',ha='center',va='center',fontsize=7,
                        color='white' if denominator and numerator/denominator>.6 else '#222222')
        cmap=plt.get_cmap('Blues').copy();cmap.set_bad('#eeeeee')
        im=ax.imshow(image,cmap=cmap,vmin=0,vmax=1,aspect='auto')
        ax.set_xticks(range(len(MARGINS)),MARGINS);ax.set_yticks(range(len(STRENGTHS)),STRENGTHS)
        ax.set_xlabel('Hazard score minus best safe score before receipt');ax.set_ylabel('Synthetic source warning score')
        ax.set_title(f'{depth} transmission'+('s' if depth>1 else ''))
    fig.suptitle('Phase 4C: hazard entries avoided / baseline hazardous choices\nOriginal floor arithmetic; four fixed seeds per cell; gray = no baseline hazard choice',fontsize=13)
    fig.colorbar(im,ax=axes.ravel().tolist(),label='Conditional avoidance fraction',shrink=.8)
    fig.savefig(directory/'strength-preference.png',dpi=150)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('--plot',action='store_true')
    args=p.parse_args();analyze(args.directory,args.plot)
