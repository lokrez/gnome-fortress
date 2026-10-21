"""Scientific figures and compact tables from the preregistered raw results."""
import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from gnome_fortress.engine import TRAITS
OUT=Path('docs/deep-time/evidence')


def read(name):
 with (OUT/name).open() as f:return list(csv.DictReader(f))


def main():
 rows=read('inheritance-generations.csv');summary=[]
 fig,axes=plt.subplots(2,3,figsize=(14,8),sharex=True,sharey=True)
 labels={'floor10':'Floor ±10','unbiased10':'Unbiased ±10','floor0':'Floor, no mutation','fertility_weighted':'Fertility-weighted floor ±10'}
 for trait,ax in zip(TRAITS,axes.flat):
  for condition,label in labels.items():
   chosen=[r for r in rows if r['trait']==trait and r['condition']==condition]
   generations=sorted({int(r['generation']) for r in chosen});samples=np.array([[float(r['mean']) for r in chosen if int(r['generation'])==g] for g in generations])
   line=ax.plot(generations,samples.mean(axis=1),label=label)[0]
   ax.fill_between(generations,np.quantile(samples,.05,axis=1),np.quantile(samples,.95,axis=1),color=line.get_color(),alpha=.12)
  ax.set_title(trait.title());ax.set_ylim(0,100);ax.grid(alpha=.2);ax.set_xlabel('Discrete toy generations');ax.set_ylabel('Population mean')
 for trait in TRAITS:
  for condition in sorted({r['condition'] for r in rows}):
   values=np.array([float(r['mean']) for r in rows if r['trait']==trait and r['condition']==condition and int(r['generation'])==1000])
   summary.append(dict(trait=trait,condition=condition,n=len(values),mean=float(values.mean()),sd=float(values.std(ddof=1)),minimum=float(values.min()),maximum=float(values.max())))
 axes[0,0].legend(fontsize=8);fig.suptitle('Inheritance-only toys: mean and 5–95% between-seed ranges (20 seeds)');fig.tight_layout();fig.savefig(OUT/'inheritance.png',dpi=170);plt.close(fig)
 with (OUT/'inheritance-summary.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
 worlds=json.loads((OUT/'ecology.json').read_text());table=[]
 fig,axes=plt.subplots(1,2,figsize=(12,5))
 for w in worlds:
  c=w['counts'];hungry=c['hungry_tick_exposures'];deaths=w['deaths'];s=deaths.get('starvation',{})
  table.append(dict(seed=w['seed'],tick=w['tick'],living=w['living'],born=w['total_born'],deaths=w['total_born']-w['living'],
     starvation=s.get('count',0),hungry_exposures=hungry,hungry_assigned=c.get('hungry_assigned',0),hungry_visible_edible=c.get('hungry_visible_edible',0),
     hungry_local_edible=c.get('hungry_local_edible',0),hungry_eat=c.get('hungry_action_eat',0),hungry_move=c.get('hungry_action_move',0),hungry_drink=c.get('hungry_action_drink',0),
     starved_visible_edible=s.get('visible_edible',0),starved_local_edible=s.get('local_edible',0),starved_prior_hazard=s.get('prior_hazard',0),food=w['final_food'],seconds=w['seconds']))
  axes[0].plot([v['tick'] for v in w['cohorts']],[v['living'] for v in w['cohorts']],marker='.',label=str(w['seed']))
  axes[1].bar(str(w['seed']),s.get('count',0),label='Starvation' if w is worlds[0] else None)
 axes[0].set(xlabel='Simulation tick',ylabel='Living population',title='Unchanged ecology');axes[0].legend(title='Seed',fontsize=8)
 axes[1].set(xlabel='Seed',ylabel='Recorded starvation deaths',title='Cause label, not exclusive causal attribution')
 fig.tight_layout();fig.savefig(OUT/'ecology.png',dpi=170);plt.close(fig)
 with (OUT/'ecology-summary.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
 # Resource pressure is an observation at fixed 10-tick sampling boundaries.
 w=worlds[0];grid=np.full((32,48),np.nan)
 for tile in w['tiles']:grid[tile['y'],tile['x']]=tile['below10']/tile['samples']
 fig,ax=plt.subplots(figsize=(10,6));im=ax.imshow(grid,vmin=0,vmax=1,cmap='magma_r');fig.colorbar(im,ax=ax,label='Fraction sampled with food <10');ax.set(title='Seed 1 productive-tile depletion, 10,000 ticks',xlabel='x',ylabel='y');fig.tight_layout();fig.savefig(OUT/'depletion-seed-1.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
