"""Preregistered isolated inheritance arithmetic, not a production rule variant."""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from gnome_fortress.engine import World,TRAITS

CONFIGS=(('floor10','floor',10,False),('unbiased10','unbiased',10,False),
         ('floor0','floor',0,False),('unbiased0','unbiased',0,False),
         ('floor5','floor',5,False),('fertility_weighted','floor',10,True))
CHECKPOINTS=(0,10,50,100,250,500,1000)


def trial(seed,config,generations=1000):
 name,rounding,magnitude,weighted=config
 traits=np.array([[a.traits[k] for k in TRAITS] for a in World(seed).agents.values()],dtype=np.int64)
 n=len(traits);pairs=np.array([(a,b) for a in range(n) for b in range(n) if a!=b])
 parent_rng=np.random.default_rng(np.random.SeedSequence([seed,1]))
 mutation_rng=np.random.default_rng(np.random.SeedSequence([seed,2]))
 rounding_rng=np.random.default_rng(np.random.SeedSequence([seed,3]))
 totals={k:np.zeros(len(TRAITS)) for k in ('parent_average','rounding_error','mutation','clamp')}
 rows=[]
 def row(generation):
  for j,k in enumerate(TRAITS):
   rows.append(dict(seed=seed,condition=name,generation=generation,trait=k,mean=float(traits[:,j].mean()),
                    sd=float(traits[:,j].std()),minimum=int(traits[:,j].min()),maximum=int(traits[:,j].max())))
 row(0)
 for generation in range(1,generations+1):
  u=parent_rng.random(n)
  if weighted:
   fertility=traits[:,TRAITS.index('fertility')]
   weights=(fertility[pairs[:,0]]+fertility[pairs[:,1]])//3
   # Zero total means no reproduction in the production threshold model. Stop
   # instead of silently creating descendants from an impossible parent pool.
   if not weights.sum():raise ValueError('No eligible reproductive probability mass')
   indexes=np.searchsorted(np.cumsum(weights)/weights.sum(),u,side='right')
  else:indexes=np.floor(u*len(pairs)).astype(int)
  chosen=pairs[indexes];sums=traits[chosen].sum(axis=1);mid=sums/2
  rounded=sums//2
  toss=rounding_rng.random(rounded.shape)
  if rounding=='unbiased':rounded=rounded+((sums%2!=0)&(toss<.5))
  mutation=np.floor(mutation_rng.random(rounded.shape)*(2*magnitude+1)).astype(int)-magnitude
  raw=rounded+mutation;child=np.clip(raw,0,100)
  for key,value in (('parent_average',mid),('rounding_error',rounded-mid),('mutation',mutation),('clamp',child-raw)):
   totals[key]+=value.mean(axis=0)
  traits=child
  if generation in CHECKPOINTS:row(generation)
 arithmetic=[dict(seed=seed,condition=name,trait=k,**{field:float(values[j]/generations) for field,values in totals.items()}) for j,k in enumerate(TRAITS)]
 return rows,arithmetic


def write_csv(path,rows):
 with path.open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('docs/deep-time/evidence'));a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 start=time.perf_counter();rows=[];arithmetic=[]
 for seed in range(1,21):
  for config in CONFIGS:
   r,b=trial(seed,config);rows.extend(r);arithmetic.extend(b)
  print('inheritance seed',seed,flush=True)
 write_csv(a.out/'inheritance-generations.csv',rows);write_csv(a.out/'inheritance-arithmetic.csv',arithmetic)
 # Matched seed bootstrap, one reproducibly independent resampling stream.
 rng=np.random.default_rng(20261021);samples=rng.integers(0,20,(10000,20));comparisons=[]
 for left,right in (('floor10','unbiased10'),('floor10','floor0'),('floor10','floor5'),('fertility_weighted','floor10'),('floor0','unbiased0')):
  for trait in TRAITS:
   values={condition:np.array([r['mean'] for r in rows if r['condition']==condition and r['trait']==trait and r['generation']==1000]) for condition in (left,right)}
   delta=values[left]-values[right];boots=delta[samples].mean(axis=1)
   comparisons.append(dict(left=left,right=right,trait=trait,n=20,mean_difference=float(delta.mean()),
     low95=float(np.quantile(boots,.025)),high95=float(np.quantile(boots,.975)),minimum=float(delta.min()),maximum=float(delta.max())))
 write_csv(a.out/'inheritance-paired.csv',comparisons)
 result=dict(seeds=list(range(1,21)),generations=1000,population=60,traits=list(TRAITS),conditions=CONFIGS,
             seconds=time.perf_counter()-start,rows=len(rows),paired_comparisons=comparisons)
 (a.out/'inheritance.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
