"""Static engineering figures from the saved, untuned matched-world results."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def figures(output):
    rows=json.loads((output/'experiments/summary.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for seed,color in zip((1,2,3),('#307da2','#b56a3d','#58945a')):
        values=[next(r for r in rows if r['seed']==seed and r['condition']==condition) for condition in 'ABCDE']
        axes[0].plot(list('ABCDE'),[r['living'] for r in values],marker='o',label=f'Seed {seed}',color=color)
        base=values[0]['living']
        axes[1].plot(list('ABCDE'),[r['living']-base for r in values],marker='o',color=color)
    axes[0].set(ylabel='Living individuals at tick 3,000',title='Three matched seeds, fixed intervention schedules')
    axes[1].set(ylabel='Living population difference versus A',title='Observed paired differences; no general benefit claim')
    axes[1].axhline(0,color='gray',linewidth=1,linestyle='--')
    for ax in axes:
        ax.set_xlabel('A untouched · B fractured · C restored · D spring · E combined',fontsize=8)
        ax.grid(axis='y',alpha=.25)
    axes[0].legend()
    fig.savefig(output/'population-comparison.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    figures(p.parse_args().output)
