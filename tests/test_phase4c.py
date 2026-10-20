import copy

import pytest

from gnome_fortress.engine import World
from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld
from research.phase4b_experiment import ThreeGnomesWorld
from research.phase4c_matrix import MatrixWorld, attenuate, divide
from research.phase4c_pilot import run_world
from research.phase4c_study import ablation
from research.phase4c_tools import MixedOrigin, masked_readout, scores


@pytest.mark.parametrize('mode,expected', [('floor',[-1,-1,0,0,1]),('truncate',[-1,0,0,0,1]),('symmetric',[-1,-1,0,1,1])])
def test_signed_division(mode,expected):
    assert [divide(n,2,mode) for n in (-2,-1,0,1,2)]==expected


def test_attenuation_floor_and_alternatives():
    assert attenuate(-11,'floor')==(-6,-2)
    assert attenuate(-2,'floor')==(-1,-1)
    for _ in range(7):assert attenuate(-1,'floor')==(-1,-1)
    assert attenuate(-1,'truncate')==(0,0)
    assert attenuate(-1,'symmetric')==(-1,0)
    assert attenuate(1,'floor')==(0,0)
    for n in range(101):
        for mode in ('truncate','symmetric'):
            assert attenuate(-n,mode)[1]==-attenuate(n,mode)[1]


def test_score_capture_and_mask_are_pure_and_do_not_touch_learning():
    w=ThreeGnomesWorld(1);w.step(2);a=w.agents[3]
    initial=copy.deepcopy(w.state()); before=scores(w,a);after=scores(w,a,ablate=True)
    assert w.state()==initial
    assert len(before)==len(after)==3
    assert sum(x[0]!=y[0] for x,y in zip(before,after))==1
    with masked_readout(w,a):
        assert a.learned.get('move:hazard')==-1
        w.remember(a,'move','hazard',-12)
        # The learning getter must see the stored -1, rather than the ablated 0.
        assert a.learned['move:hazard']==-4
    assert a.learned['move:hazard']==-4
    with pytest.raises(MixedOrigin):scores(w,a,ablate=True)


@pytest.mark.parametrize('depth',[1,2,3,7])
def test_matrix_geometry_margins_and_restoration(depth):
    w=MatrixWorld(1,depth)
    for margin in (-8,-4,-2,-1,0,1,2,4,8,16,32,50):
        w.reset(-64,margin); initial=World.state(w)
        candidates=scores(w,w.agents[w.target_id])
        assert len(candidates)==4
        hazardous=[s for s,x,y in candidates if w.cell(x,y).terrain=='hazard']
        safe=[s for s,x,y in candidates if w.cell(x,y).terrain=='grass']
        assert len(hazardous)==1 and len(safe)==3 and hazardous[0]-max(safe)==margin
        row=w.case(-64,margin,'floor','multihop')
        assert row['target_delivered'] and row['firsthand_before']==0
        assert len(row['receipts'])==depth
        assert all(abs(r['source_xy'][0]-r['recipient_xy'][0])+abs(r['source_xy'][1]-r['recipient_xy'][1])==1 for r in row['receipts'])
        w.reset(-64,margin)
        assert World.state(w)==initial


def test_matrix_controls_conflicting_preferences_and_zero():
    w=MatrixWorld(2,2)
    rows={c:w.case(-64,1,'floor',c) for c in ('individual','direct','multihop','masked','irrelevant','ablation')}
    assert len({r['rng_before'] for r in rows.values()})==1
    assert len({r['unrelated_before'] for r in rows.values()})==1
    assert rows['individual']['chosen_terrain']=='hazard'
    assert rows['direct']['chosen_terrain']=='hazard'
    assert rows['multihop']['chosen_terrain']=='grass'
    assert rows['ablation']['chosen_terrain']=='hazard'
    assert rows['masked']['chosen_terrain']=='hazard'
    assert rows['irrelevant']['chosen_terrain']=='hazard'
    assert rows['multihop']==w.case(-64,1,'floor','multihop')
    assert not w.case(0,0,'floor','multihop')['target_delivered']
    assert not w.case(-1,0,'truncate','multihop')['target_delivered']
    assert w.case(-1,0,'floor','multihop')['acquired_hazard']==-1
    # A warning cannot reverse a preference margin larger than its magnitude.
    assert not w.case(-64,50,'floor','multihop')['decision_changed']


@pytest.mark.parametrize('seed',[1,2,3])
def test_original_boundary_identical_and_replay(seed):
    rows=ablation(seed)
    assert rows==ablation(seed)
    assert rows[0]['full_boundary']==rows[1]['full_boundary']
    assert rows[0]['actor_before']==rows[1]['actor_before']
    assert rows[0]['firsthand_before']==rows[1]['firsthand_before']==0
    assert rows[0]['stored_hazard']==rows[1]['stored_hazard']==-1


@pytest.mark.parametrize('condition',['individual','direct','multihop','masked'])
def test_pilot_observation_does_not_change_world(condition):
    measured,world,_=run_world(1,condition,ticks=50)
    reference=TelephoneWorld(1,TelephoneConfig(condition));reference.step(50)
    assert world.state()==reference.state()
    replay,_,_=run_world(1,condition,ticks=50)
    assert measured==replay
    assert len(measured['examples'])<=8
    assert len(measured['recipients'])<=len(world.agents)
    assert measured['slots']==60


def test_floor_harness_matches_actual_phase4b_receipt_values():
    for seed in (1,11,32,64):
        w=ThreeGnomesWorld(seed);w.step(2)
        proof=w.proofs[3]['move:hazard'];value=proof['root']['value']
        for receipt in proof['receipts']:
            packet,value=attenuate(value,'floor')
            assert (packet,value)==(receipt['transmitted'],receipt['after'])
        actual=MatrixWorld(seed,2).case(proof['root']['value'],0,'floor','multihop')
        assert actual['acquired_hazard']==value


def test_no_candidates_capture_and_firsthand_only_are_nonmutating():
    w=MatrixWorld(1,2);w.reset(-64,0);a=w.agents[1]
    before=World.state(w)
    assert scores(w,a,ablate=True)==scores(w,a)
    assert World.state(w)==before
    c=w.agents[w.target_id]
    for x,y in w.neighbors(c.x,c.y):w.cell(x,y).terrain='rock'
    before=World.state(w)
    assert scores(w,c)==[] and World.state(w)==before


def test_competition_threshold_is_original_score_addition():
    w=MatrixWorld(3,1)
    for margin in (-1,0,1,2,4,8,16):
        row=w.case(-64,margin,'floor','multihop')
        hazard=max(s for s,x,y in row['after'] if w.cell(x,y).terrain=='hazard')
        safe=max(s for s,x,y in row['after'] if w.cell(x,y).terrain=='grass')
        assert hazard-safe==margin-8
        if margin<8:assert row['chosen_terrain']=='grass'
        elif margin>8:assert row['chosen_terrain']=='hazard'
