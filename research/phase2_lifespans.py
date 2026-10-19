"""Descriptive registered secondary lifetime summaries, with censoring separate."""
import csv
from pathlib import Path
import numpy as np
from research.study import write_csv

ROOT=Path('research/phase2')


def main():
    rows=[]
    for study,expected in (('memory',40),('scaling',15),('endurance',3)):
        folders=sorted(p.parent for p in (ROOT/'data'/study).glob('*/summary.json'))
        assert len(folders)==expected
        for folder in folders:
            with (folder/'agents.csv').open() as stream:
                agents=list(csv.DictReader(stream))
            classified=0
            for founder in (True,False):
                for died in (True,False):
                    group=[a for a in agents if bool(int(a['founder']))==founder and bool(int(a['died']))==died]
                    classified+=len(group)
                    row=dict(study=study,run=folder.name,seed=agents[0]['seed'],
                             memory=agents[0]['memory'],slots=agents[0]['slots'],
                             cohort='founder' if founder else 'offspring',
                             status='completed death' if died else 'right censored alive',count=len(group))
                    for field,prefix in (('age_ticks','biological_age'),('observed_ticks','observed_time')):
                        values=np.array([int(a[field]) for a in group],dtype=int)
                        for quantile,name in ((0,'min'),(.1,'q10'),(.5,'median'),(.9,'q90'),(1,'max')):
                            row[f'{prefix}_{name}']=float(np.quantile(values,quantile)) if len(values) else None
                    rows.append(row)
            assert classified==len(agents)
    write_csv(ROOT/'results/lifespan-distributions.csv',rows)
    print(f'Lifetime summaries: {len(rows)} cohort/status rows across 58 runs; all agents accounted for')


if __name__=='__main__':
    main()
