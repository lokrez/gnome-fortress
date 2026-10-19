"""Static measured comparisons; no inferred confidence from single timing runs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path('research/phase3')


def main():
    rows=json.loads((ROOT/'benchmark-results.json').read_text())
    pairs={}
    for row in rows:pairs.setdefault(row['name'],{})[row['variant']]=row
    output=[]
    for name,pair in pairs.items():
        a,b=pair['reference'],pair['optimized']
        output.append(dict(name=name,tick=a['start_tick'],reference_tps=a['ticks_per_second'],optimized_tps=b['ticks_per_second'],
            speedup=b['ticks_per_second']/a['ticks_per_second'],reference_first_save=a['first_save_seconds'],optimized_first_save=b['first_save_seconds'],
            reference_repeated_save=a['repeated_save_seconds'],optimized_repeated_save=b['repeated_save_seconds'],
            repeated_save_speedup=a['repeated_save_seconds']/b['repeated_save_seconds'],
            reference_load_peak_mib=a['load_peak_rss_mib'],optimized_load_peak_mib=b['load_peak_rss_mib'],
            reference_file_mib=a['file_bytes']/1024**2,optimized_file_mib=b['file_bytes']/1024**2))
    (ROOT/'comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','svg.hashsalt':'gnome-phase3'})
    fig,axes=plt.subplots(1,3,figsize=(14,4.8))
    x=np.arange(len(output));labels=['Young\nseed 11','20k\nseed 1','100k\nseed 1','100k\nseed 2','100k\nseed 3']
    for ax,keys,title,ylabel in zip(axes,[('reference_tps','optimized_tps'),('reference_repeated_save','optimized_repeated_save'),('reference_load_peak_mib','optimized_load_peak_mib')],
        ['Headless execution','Repeated complete checkpoint','Fresh-process load high-water RSS'],['Ticks per second','Seconds','MiB']):
        for offset,key,color,label in zip((-.18,.18),keys,('#8d99ae','#287d8e'),('Phase 2 reference','Phase 3')):
            ax.bar(x+offset,[r[key] for r in output],width=.36,color=color,label=label)
        ax.set(xticks=x,xticklabels=labels,title=title,ylabel=ylabel);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
    axes[0].legend(fontsize=8)
    fig.suptitle('Sequential fresh processes on the Ryzen 7 3800X; exact logical outcomes matched',fontsize=12)
    fig.tight_layout();fig.savefig(ROOT/'performance.png',dpi=160,bbox_inches='tight')
    fig.savefig(ROOT/'performance.svg',bbox_inches='tight',metadata={'Date':'2026-10-19'})
    p=ROOT/'performance.svg';p.write_text('\n'.join(s.rstrip() for s in p.read_text().splitlines())+'\n')
    print(json.dumps(output,indent=2))

if __name__=='__main__':main()
