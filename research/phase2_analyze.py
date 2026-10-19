"""Pre-specified paired analysis and descriptive scaling/endurance figures."""
import argparse
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import t as student_t

from research.study import write_csv

ROOT=Path('research/phase2')
CAUSES=('old_age','starvation','dehydration','hazard')


def read_csv(path):
    with path.open() as f:
        rows=list(csv.DictReader(f))
    for row in rows:
        for key,val in row.items():
            try:
                row[key]=float(val) if val else None
            except ValueError:
                pass
    return rows


def column(rows,key):
    return np.array([r[key] for r in rows],dtype=float)


def figure(fig,name):
    out=ROOT/'results'
    fig.savefig(out/f'{name}.png',dpi=160,bbox_inches='tight')
    path=out/f'{name}.svg'
    fig.savefig(path,bbox_inches='tight',metadata={'Date':'2026-10-19'})
    path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)


def outcome(folder):
    summary=json.loads((folder/'summary.json').read_text())
    perf=json.loads((folder/'performance.json').read_text())
    counters=summary['extension_counters']
    pop=read_csv(folder/'population.csv')
    horizon=summary['ticks']
    tail=[r for r in pop if r['tick']>horizon-5000]
    rows=dict(seed=summary['seed'],memory=summary['memory'],slots=summary['slots'],
              final_population=summary['final_population'],offspring=summary['offspring'],deaths=summary['deaths'],
              complete_cohort_mean_age=summary['complete_cohort_mean_age'],complete_cohort_n=summary['complete_cohort_n'],
              hazards_per_1000_decisions=counters.get('hazard',0)/counters['decisions']*1000,
              deaths_per_1000_agent_ticks=counters.get('death',0)/counters['agent_ticks']*1000,
              offspring_per_1000_agent_ticks=counters.get('birth',0)/counters['agent_ticks']*1000,
              agent_ticks=counters['agent_ticks'],decisions=counters['decisions'],
              assigned_utilization=counters['decisions']/counters['capacity'],
              retained_utilization=counters['retained']/counters['capacity'],
              waiting_fraction=1-counters['decisions']/counters['eligible'],
              decisions_per_agent_tick=counters['decisions']/counters['agent_ticks'],
              mean_eligible_population=counters['eligible']/(horizon-summary['start_tick']),
              mean_living_population=counters['agent_ticks']/(horizon-summary['start_tick']),
              sleep_events=counters.get('sleep',0),wake_events=counters.get('wake',0),
              mean_tail_population=float(np.mean(column(tail,'living'))),
              final_food_stock=pop[-1]['food_stock'],max_generation=summary['max_generation'],
              final_digest=summary['final_digest'],initial_digest=summary['initial_digest'],
              initial_biological_digest=summary['initial_biological_digest'],
              full_replay=bool(summary.get('full_replay',{}).get('equal',False)),
              **{key:perf[key] for key in ('loop_wall_seconds','loop_cpu_seconds','ticks_per_second',
                 'simulation_peak_rss_mib','overall_peak_rss_mib','cpu_percent_one_core','cpu_percent_16_logical',
                 'scheduler_seconds','scheduler_fraction_of_loop')})
    for cause in CAUSES:
        rows['deaths_'+cause]=summary['death_causes'].get(cause,0)
        rows[cause+'_per_1000_agent_ticks']=counters.get('cause:'+cause,0)/counters['agent_ticks']*1000
    return rows,pop


def paired_effect(a,b,resamples):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    assert len(a)==len(b) and len(a)>1 and np.all(np.isfinite(a)) and np.all(np.isfinite(b))
    d=a-b
    boot=np.mean(d[resamples],axis=1)
    low,high=np.quantile(boot,[.025,.975])
    se=np.std(d,ddof=1)/np.sqrt(len(d))
    critical=student_t.ppf(.975,len(d)-1)
    return dict(n_pairs=len(d),enabled_mean=float(np.mean(a)),ablated_mean=float(np.mean(b)),
                mean_paired_difference=float(np.mean(d)),median_paired_difference=float(np.median(d)),
                bootstrap_95_low=float(low),bootstrap_95_high=float(high),
                paired_t_95_low=float(np.mean(d)-critical*se),paired_t_95_high=float(np.mean(d)+critical*se),
                positive_pairs=int(sum(d>0)),negative_pairs=int(sum(d<0)),
                percent_mean_change=float((np.mean(a)/np.mean(b)-1)*100) if np.mean(b) else None)


def analyze_memory():
    rows=[]
    for seed in range(1001,1021):
        pair=[]
        for condition in ('enabled','ablated'):
            row,_=outcome(ROOT/f'data/memory/seed-{seed}-{condition}')
            rows.append(row); pair.append(row)
        assert pair[0]['initial_digest']==pair[1]['initial_digest']
        assert pair[0]['slots']==pair[1]['slots']==60
    write_csv(ROOT/'results/memory-seeds.csv',rows)
    enabled=[r for r in rows if r['memory']=='enabled']
    ablated=[r for r in rows if r['memory']=='ablated']
    metrics=('complete_cohort_mean_age','hazards_per_1000_decisions','final_population','mean_tail_population',
             'deaths_per_1000_agent_ticks','starvation_per_1000_agent_ticks','dehydration_per_1000_agent_ticks',
             'hazard_per_1000_agent_ticks','old_age_per_1000_agent_ticks','offspring_per_1000_agent_ticks',
             'offspring','deaths','deaths_starvation','deaths_hazard','decisions_per_agent_tick')
    indices=np.random.default_rng(20261019).integers(0,20,size=(10000,20))
    effects=[]
    for metric in metrics:
        effects.append(dict(metric=metric,**paired_effect([r[metric] for r in enabled],[r[metric] for r in ablated],indices)))
    write_csv(ROOT/'results/memory-effects.csv',effects)
    paired=[]
    for a,b in zip(enabled,ablated):
        row=dict(seed=a['seed'])
        for metric in metrics:
            row[metric+'_enabled']=a[metric]
            row[metric+'_ablated']=b[metric]
            row[metric+'_difference']=a[metric]-b[metric]
        paired.append(row)
    write_csv(ROOT/'results/memory-pairs.csv',paired)
    fig,axes=plt.subplots(2,3,figsize=(13,8))
    selected=(('complete_cohort_mean_age','Complete newborn-cohort lifespan','Mean age at death (ticks)'),
              ('hazards_per_1000_decisions','Hazard exposure','Entries / 1,000 own decisions'),
              ('final_population','Population at 20,000 ticks','Living gnomes'),
              ('deaths_per_1000_agent_ticks','All mortality','Deaths / 1,000 agent-ticks'),
              ('starvation_per_1000_agent_ticks','Recorded starvation mortality','Deaths / 1,000 agent-ticks'),
              ('offspring_per_1000_agent_ticks','Reproduction','Births / 1,000 agent-ticks'))
    for ax,(metric,title,label) in zip(axes.flat,selected):
        for a,b in zip(enabled,ablated):
            ax.plot([0,1],[b[metric],a[metric]],color='#8a9ba8',alpha=.55,lw=.8)
        ax.scatter(np.zeros(20),[r[metric] for r in ablated],color='#d1495b',s=16,zorder=3)
        ax.scatter(np.ones(20),[r[metric] for r in enabled],color='#287d8e',s=16,zorder=3)
        ax.set(xticks=[0,1],xticklabels=['Ablated','Enabled'],ylabel=label,title=title,xlim=(-.3,1.3))
    fig.suptitle('20 matched world seeds, 20,000 ticks; 60 slots in both conditions',fontsize=14)
    fig.tight_layout()
    figure(fig,'memory-paired')
    return effects


def analyze_scaling():
    rows=[]
    for slots in (60,120,240,480,960):
        for seed in (11,12,13):
            row,_=outcome(ROOT/f'data/scaling/seed-{seed}-slots-{slots}')
            rows.append(row)
    for seed in (11,12,13):
        assert len({r['initial_biological_digest'] for r in rows if r['seed']==seed})==1
    assert all(r['full_replay'] for r in rows if r['seed']==11)
    write_csv(ROOT/'results/scaling.csv',rows)
    fig,axes=plt.subplots(2,3,figsize=(13,8))
    measures=(('ticks_per_second','Headless throughput','World ticks / second'),
              ('simulation_peak_rss_mib','Fresh-process simulation peak RSS','MiB'),
              ('scheduler_fraction_of_loop','Scheduler share of measured loop','Fraction of wall time'),
              ('final_population','Behavioral outcome: population','Living at tick 3,000'),
              ('decisions_per_agent_tick','Actual decision opportunities','Own decisions / biological agent-tick'),
              ('assigned_utilization','Logical capacity used','Assigned decisions / available slots'))
    for ax,(metric,title,label) in zip(axes.flat,measures):
        for seed,color in zip((11,12,13),('#287d8e','#d1495b','#e6a23c')):
            data=[r for r in rows if r['seed']==seed]
            ax.plot([r['slots'] for r in data],[r[metric] for r in data],marker='o',label=str(seed),color=color)
        ax.set_xscale('log',base=2)
        ax.set(xticks=[60,120,240,480,960],xticklabels=['60','120','240','480','960'],title=title,xlabel='Logical slots',ylabel=label)
    axes[0,0].legend(title='Seed')
    fig.suptitle('Sequential fresh-process benchmarks; 3,000 ticks per world (different behavioral conditions)',fontsize=13)
    fig.tight_layout(); figure(fig,'scaling')
    synthetic=[]
    for path in sorted((ROOT/'data/synthetic').glob('*.json')):
        row=json.loads(path.read_text()); row.pop('block_microseconds')
        synthetic.append(row)
    write_csv(ROOT/'results/scheduler-only.csv',synthetic)
    fig,ax=plt.subplots(figsize=(8,4.5))
    for n in (960,3840):
        data=sorted([r for r in synthetic if r['total_identities']==n],key=lambda r:r['slots'])
        ax.plot([r['slots'] for r in data],[r['microseconds_per_call'] for r in data],marker='o',label=f'{n} fixed identities; {data[0]["eligible"]} eligible')
    ax.set_xscale('log',base=2)
    ax.set(xticks=[60,120,240,480,960],xticklabels=['60','120','240','480','960'],xlabel='Logical slots',ylabel='Microseconds / schedule call',title='Scheduler-only synthetic workload (10,000 calls per fresh process)')
    ax.legend(); fig.tight_layout(); figure(fig,'scheduler-only')
    return rows


def analyze_endurance():
    summaries=[]
    fig,axes=plt.subplots(3,2,figsize=(13,11))
    for seed,color in zip((1,2,3),('#287d8e','#d1495b','#e6a23c')):
        folder=ROOT/f'data/endurance/seed-{seed:02d}'
        row,pop=outcome(folder)
        summary=json.loads((folder/'summary.json').read_text())
        assert summary['start_tick']==20000 and summary['ticks']==100000
        checks=json.loads((folder/'checkpoints.json').read_text())
        assert {c['tick'] for c in checks}=={50000,100000}
        assert all(c['exact_load'] and c['exact_replay'] for c in checks)
        prefix=read_csv(Path(f'research/phase1/data/seed-{seed:02d}/population.csv'))
        full=prefix[:-1]+pop
        x,y=column(full,'tick'),column(full,'living')
        tail=x>=80000
        slope,intercept=np.polyfit(x[tail]/1000,y[tail],1)
        row.update(tail_80000_mean=float(np.mean(y[tail])),tail_80000_min=float(min(y[tail])),
                   tail_80000_max=float(max(y[tail])),tail_80000_slope_per_1000=float(slope),
                   previous_10000_mean=float(np.mean(y[(x>80000)&(x<=90000)])),
                   final_10000_mean=float(np.mean(y[x>90000])),
                   exact_checkpoint_replays=True)
        summaries.append(row)
        axes[0,0].plot(x,y,label=str(seed),color=color,lw=1)
        tx=column(pop,'tick')
        axes[0,1].plot(tx,column(pop,'food_stock'),color=color,lw=1)
        # Rate windows use every recorded 1,000-tick block in the extension.
        rates=[]
        for end in range(21000,100001,1000):
            block=[r for r in pop if end-1000<r['tick']<=end]
            exposure=sum(r['agent_ticks'] for r in block)
            rates.append(dict(tick=end,births=sum(r['births_interval'] for r in block),
                              deaths=sum(r['deaths_interval'] for r in block),
                              starvation=sum(r['starvation_deaths'] for r in block)/exposure*1000,
                              decisions=sum(r['decisions'] for r in block)/exposure,
                              hunger_fraction=float(np.mean([r['hunger_over_100']/r['living'] if r['living'] else 0 for r in block]))))
        axes[1,0].plot([r['tick'] for r in rates],[r['births'] for r in rates],color=color,lw=.8,label=f'{seed} births')
        axes[1,0].plot([r['tick'] for r in rates],[r['deaths'] for r in rates],color=color,lw=.8,ls='--',label=f'{seed} deaths')
        axes[1,1].plot([r['tick'] for r in rates],[r['starvation'] for r in rates],color=color,lw=1)
        axes[2,0].plot(tx,column(pop,'mean_alive_generation'),color=color,lw=1,label=f'{seed} living mean')
        axes[2,0].plot(tx,column(pop,'max_generation'),color=color,lw=.8,ls='--')
        axes[2,1].plot([r['tick'] for r in rates],[r['decisions'] for r in rates],color=color,lw=1)
        write_csv(ROOT/f'results/endurance-seed-{seed}-windows.csv',rates)
    write_csv(ROOT/'results/endurance.csv',summaries)
    titles=(('Population through 100,000 ticks','Living gnomes'),('Actual food stock (extension only)','Food units'),
            ('Birth/death balance: solid births, dashed deaths','Events / 1,000 ticks'),('Recorded starvation pressure','Deaths / 1,000 agent-ticks'),
            ('Generations: solid living mean, dashed maximum','Ancestry generation'),('Scheduler opportunities per living exposure','Own decisions / biological agent-tick'))
    for ax,(title,label) in zip(axes.flat,titles):
        ax.set(title=title,xlabel='World tick',ylabel=label)
    axes[0,0].axvspan(0,20000,color='gray',alpha=.12,label='Verified Phase 1 prefix')
    axes[0,0].legend(fontsize=8)
    fig.suptitle('Original enabled 60-slot baseline; three seeds; no extinction recovery',fontsize=14)
    fig.tight_layout(); figure(fig,'endurance')
    return summaries


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--only',choices=['memory','scaling','endurance','all'],default='all')
    args=parser.parse_args()
    (ROOT/'results').mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.2,'svg.fonttype':'none','svg.hashsalt':'gnome-fortress-phase2'})
    result={}
    if args.only in ('memory','all'): result['memory_effects']=analyze_memory()
    if args.only in ('scaling','all'): result['scaling_runs']=analyze_scaling()
    if args.only in ('endurance','all'): result['endurance_runs']=analyze_endurance()
    (ROOT/f'analysis-{args.only}.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
