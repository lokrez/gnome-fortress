"""Declared descriptive supplement; primary paired analysis remains unchanged."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest

from research.phase2_analyze import ROOT, figure, read_csv
from research.study import write_csv


def main():
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.2,'svg.fonttype':'none','svg.hashsalt':'gnome-fortress-phase2'})
    rows=[]
    fig,axes=plt.subplots(1,2,figsize=(12,4.5),gridspec_kw={'width_ratios':[2,1]})
    intervals=[]
    for condition,color in (('enabled','#287d8e'),('ablated','#d1495b')):
        k=0
        for seed in range(1001,1021):
            folder=ROOT/f'data/memory/seed-{seed}-{condition}'
            summary=json.loads((folder/'summary.json').read_text())
            extinct=summary['final_population']==0
            k+=int(extinct)
            extinction_tick=None
            if extinct:
                with (folder/'agents.csv').open() as f:
                    agents=list(csv.DictReader(f))
                assert all(int(a['died']) for a in agents)
                extinction_tick=max(int(a['end_tick']) for a in agents)
            rows.append(dict(seed=seed,memory=condition,extinct=int(extinct),extinction_tick=extinction_tick,
                             observation_ticks=20000,final_population=summary['final_population']))
            pop=read_csv(folder/'population.csv')
            axes[0].plot([r['tick'] for r in pop],[r['living'] for r in pop],color=color,alpha=.35,lw=.8,
                         label=condition if seed==1001 else None)
        ci=binomtest(k,20).proportion_ci(confidence_level=.95,method='exact')
        intervals.append(dict(memory=condition,extinct_worlds=k,n_worlds=20,fraction=k/20,
                              binomial_95_low=ci.low,binomial_95_high=ci.high,
                              interpretation='Exploratory within-condition binomial reference; not paired risk-difference CI'))
    axes[0].set(title='All 40 observed population trajectories',xlabel='World tick',ylabel='Living gnomes')
    axes[0].legend()
    for i,row in enumerate(intervals):
        y=row['fraction']
        axes[1].errorbar(i,y,yerr=[[y-row['binomial_95_low']],[row['binomial_95_high']-y]],fmt='o',capsize=5,
                         color='#287d8e' if row['memory']=='enabled' else '#d1495b')
    axes[1].set(xticks=[0,1],xticklabels=['Enabled','Ablated'],ylim=(-.05,1.05),
                ylabel='Worlds extinct by 20,000 ticks',title='Observed extinction fractions\nExact binomial 95% reference intervals')
    fig.tight_layout(); figure(fig,'memory-extinction')
    write_csv(ROOT/'results/memory-extinction-seeds.csv',rows)
    write_csv(ROOT/'results/memory-extinction-intervals.csv',intervals)
    print(json.dumps(intervals,indent=2))


if __name__=='__main__':
    main()
