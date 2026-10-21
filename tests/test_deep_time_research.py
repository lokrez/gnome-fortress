"""The experiment monitor observes real actions; arithmetic stays research-only."""
import numpy as np
from research.deep_time.inheritance import trial,CONFIGS
from research.deep_time.ecology import run,digest
from gnome_fortress.terrain_game import TerrainWorld


def test_mathematical_trial_replay_and_floor_error():
    config=CONFIGS[0]
    a,terms=trial(7,config,generations=10)
    b,again=trial(7,config,generations=10)
    assert a==b and terms==again
    assert all(-.5<=r['rounding_error']<=0 for r in terms)
    assert all(0<=r['minimum']<=r['maximum']<=100 for r in a)


def test_observational_monitor_deaths_and_continuation_exact():
    reference=TerrainWorld(1);reference.step(3000)
    observed,result=run(1,3000)
    assert digest(reference)==digest(observed)==result['digest']
    assert sum(d['count'] for d in result['deaths'].values())==sum(not a.alive for a in observed.agents.values())
    assert len(result['examples'])<=128
    count=result['counts']
    assert count['hungry_assigned']<=count['hungry_awake']<=count['hungry_tick_exposures']
    assert count['actual_decisions']==sum(v for k,v in count.items() if k.startswith('action_'))
    assert sum(d['hungry_opportunities'] for d in result['deaths'].values())<=count['hungry_assigned']
    assert sum(a.alive for a in observed.agents.values())+sum(d['count'] for d in result['deaths'].values())==len(observed.agents)
    reference.step(30);observed.step(30)
    assert digest(reference)==digest(observed)


def test_fixed_mutation_and_rounding_expectations():
    # Exhaustive arithmetic, not a sampled claim of unbiasedness. The actual
    # population trials use this same floor operation on parent integer sums.
    for total in range(201):
        floor=total//2
        assert floor-total/2==(-.5 if total%2 else 0)
        alternatives=[floor,floor+1] if total%2 else [floor,floor]
        assert np.mean(alternatives)==total/2
    assert sum(range(-10,11))==0
    # Bounds induce inward bias even for an unbiased pre-clamp mutation.
    assert np.mean([max(0,x) for x in range(-10,11)])>0
    assert np.mean([min(100,100+x) for x in range(-10,11)])<100
