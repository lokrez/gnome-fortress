"""Independent archive/telemetry/configuration reconciliation for Phase 2."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess

from research.phase2_controls import Config, capacity, load_experiment
from research.study import write_csv

ROOT=Path('research/phase2')


def verify(folder):
    summary=json.loads((folder/'summary.json').read_text())
    cfg=Config(**summary['config'])
    with capacity(cfg.slots):
        w=load_experiment(folder/'final.sqlite',cfg)
        assert w.digest()==summary['final_digest']
        events=Counter(e.kind for e in w.events)
        causes=Counter(a.death_cause for a in w.agents.values() if not a.alive)
        assert dict(events)==summary['events'] and dict(causes)==summary['death_causes']
        assert len(w.agents)==summary['total_births']
        assert len(w.living())==summary['final_population']
        changes=[0]*(w.tick+1)
        births=[0]*(w.tick+1)
        deaths=[0]*(w.tick+1)
        for e in w.events:
            if e.kind=='birth': changes[e.tick]+=1; births[e.tick]+=1
            elif e.kind=='death': changes[e.tick]-=1; deaths[e.tick]+=1
        stock=nb=nd=0
        population=[]
        for i in range(w.tick+1):
            stock+=changes[i]; nb+=births[i]; nd+=deaths[i]
            population.append(stock)
            births[i],deaths[i]=nb,nd
        assert population[0]==60 and stock==len(w.living())
        exposure_prefix=[0]
        for p in population[:-1]: exposure_prefix.append(exposure_prefix[-1]+p)
        with (folder/'population.csv').open() as f:
            samples=list(csv.DictReader(f))
        previous=summary['start_tick']
        for i,row in enumerate(samples):
            tick=int(row['tick'])
            assert int(row['living'])==population[tick]
            assert int(row['births_total'])==births[tick]
            assert int(row['deaths_total'])==deaths[tick]
            assert int(row['agent_ticks'])==exposure_prefix[tick]-exposure_prefix[previous]
            if i:
                assert int(row['births_interval'])==births[tick]-births[previous]
                assert int(row['deaths_interval'])==deaths[tick]-deaths[previous]
            assert int(row['retained_slot_ticks'])<=int(row['decisions'])<=int(row['capacity_slot_ticks'])
            assert int(row['eligible_agent_ticks'])>=int(row['decisions'])
            previous=tick
        counters=summary['extension_counters']
        assert sum(int(r['decisions']) for r in samples)==counters['decisions']
        assert sum(int(r['hazards']) for r in samples)==counters.get('hazard',0)
        assert sum(int(r['starvation_deaths']) for r in samples)==counters.get('cause:starvation',0)
        extension=Counter(e.kind for e in w.events if e.tick>summary['start_tick'])
        for key,value in extension.items(): assert counters[key]==value
        with (folder/'agents.csv').open() as f:
            agents=list(csv.DictReader(f))
        assert len(agents)==len(w.agents)
        generation={}
        for row in agents:
            a=w.agents[int(row['agent'])]
            assert int(row['age_ticks'])==a.age
            assert int(row['children'])==a.children
            assert int(row['died'])==int(not a.alive)
            generation[a.id]=0 if not a.parents else 1+max(generation[p] for p in a.parents)
            assert int(row['generation'])==generation[a.id]
            assert int(row['initial_age'])+int(row['observed_ticks'])==a.age
        assert sum(int(a['children']) for a in agents)==2*(len(agents)-60)
        assert sum(int(a['hazard_entries']) for a in agents)==counters.get('hazard',0)
        complete=[a for a in w.agents.values() if a.parents and a.born<=w.tick-3000]
        assert len(complete)==summary['complete_cohort_n'] and all(not a.alive for a in complete)
        if complete:
            assert sum(a.age for a in complete)/len(complete)==summary['complete_cohort_mean_age']
        return dict(run=str(folder),seed=w.seed,memory=cfg.memory,slots=cfg.slots,ticks=w.tick,
                    final_digest=w.digest(),exact_archive=True,exact_samples=True,exact_ancestry=True,
                    all_tick_min=min(population),all_tick_peak=max(population),extinct_ticks=sum(p==0 for p in population),
                    tail_min=min(population[max(0,w.tick-20000):]),tail_max=max(population[max(0,w.tick-20000):]),
                    max_generation=max(generation.values()))


def main():
    subprocess.run(['git','diff','--exit-code','f32c1a6','--','gnome_fortress','tests','pyproject.toml','requirements-tested.txt'],check=True)
    subprocess.run(['git','diff','--exit-code','232dd30','--','research/phase1','research/study.py','research/analyze.py','research/verify.py','research/test_study.py','research/test_analysis.py'],check=True)
    checks=[]
    for study,expected in (('scaling',15),('memory',40),('endurance',3)):
        folders=sorted(p.parent for p in (ROOT/'data'/study).glob('*/summary.json'))
        assert len(folders)==expected
        for folder in folders:
            checks.append(verify(folder))
            print('RECONCILED',folder,flush=True)
    write_csv(ROOT/'results/archive-checks.csv',checks)
    manifests={}
    for name in ('scaling','science'):
        manifest=json.loads((ROOT/f'{name}-manifest.json').read_text())
        manifests[name]={path:hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
                         for path,digest in manifest['code_hashes'].items()}
        assert all(manifests[name].values())
    (ROOT/'results/verification.json').write_text(json.dumps(dict(runs=len(checks),all_archives_reconciled=True,
        baseline_and_phase1_unchanged=True,manifest_source_hashes=manifests),indent=2,sort_keys=True)+'\n')


if __name__=='__main__':
    main()
