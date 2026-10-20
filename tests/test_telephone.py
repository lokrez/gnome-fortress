import copy
import sqlite3

import pytest

from gnome_fortress.engine import World
from gnome_fortress.telephone import (AUDIT_LIMIT, MAX_PATH, TelephoneConfig, TelephoneWorld,
                                     save_telephone, load_telephone)
from research.phase4b_experiment import ThreeGnomesWorld, comparison_state, load_probe, probe


def test_chain_changes_actual_c_movement_and_content_control():
    changes=[]
    for seed in range(1,17):
        group={c:probe(seed,c) for c in ('individual','direct','multihop','masked','irrelevant')}
        assert all(g[2]==group['individual'][2] for g in group.values())
        assert comparison_state(group['individual'][1])==comparison_state(group['masked'][1])
        assert all(comparison_state(group[c][1])['agents'][2]==comparison_state(group['individual'][1])['agents'][2]
                   for c in ('direct','masked'))
        assert group['individual'][1].rng.getstate()==group['direct'][1].rng.getstate()==group['masked'][1].rng.getstate()
        row,w,_=group['multihop']
        assert row['firsthand_c_before']==0 and row['hazard_entry']==0
        assert row['decisions']==8 and row['opportunities']==2
        assert row['meaningful_two_hop']==1
        proof=w.proofs[3]['move:hazard']
        assert proof['path']==[1,2,3]
        assert w.origins[2]['move:hazard']['firsthand_count']==0
        assert w.origins[3]['move:hazard']['firsthand_count']==0
        assert row['a_value'] < row['b_value'] < row['c_hazard_value_before'] < 0
        assert group['irrelevant'][0]['hazard_entry']==1
        assert group['irrelevant'][0]['c_hazard_value_before']==0
        assert group['irrelevant'][0]['c_grass_value_before']<0
        if group['individual'][0]['hazard_entry']: changes.append(seed)
    assert changes


def test_baseline_off_unchanged_and_phase4a_stays_no_forwarding():
    from gnome_fortress.communication import CommunicationWorld
    a,b,c=TelephoneWorld(7),World(7),CommunicationWorld(7)
    a.step(100);b.step(100);c.step(100)
    assert World.state(a)==b.state()==World.state(c)
    assert len(a.slots)==60


@pytest.mark.parametrize('condition',['individual','direct','multihop','masked','irrelevant'])
def test_deterministic_replay_and_mid_chain_reload(tmp_path,condition):
    a=ThreeGnomesWorld(1,condition); b=ThreeGnomesWorld(1,condition)
    a.step();b.step()
    path=tmp_path/'mid.sqlite';save_telephone(a,path)
    before=path.read_bytes(); loaded=load_probe(path)
    assert path.read_bytes()==before and loaded.state()==a.state()
    a.step(2);b.step(2);loaded.step(2)
    assert a.state()==b.state()==loaded.state()
    assert a.digest()==loaded.digest()


def test_duplicates_and_loops_cannot_reinforce_and_history_is_bounded():
    w=ThreeGnomesWorld(1);w.step(2)
    a,b,c=[w.agents[i] for i in (1,2,3)]
    # B is beside C; repeated B->C receipts cannot strengthen C.
    old=c.learned['move:hazard']; count=w.messages
    event_count=len(w.events)
    for _ in range(2000):assert not w.contact(b,c)
    assert c.learned['move:hazard']==old and w.messages==count
    assert len(w.audit)==AUDIT_LIMIT and len(w.events)==event_count
    # C->B is a path loop, not a second independent source.
    assert not w.contact(c,b) and w.audit[-1]['reason']=='loop'
    a.x,a.y=4,3
    assert not w.contact(b,a) and w.audit[-1]['reason']=='loop'
    assert len(w.proofs[3]['move:hazard']['receipts'])==2


def test_impossible_missing_dead_sleeping_and_interrupted_delivery():
    w=ThreeGnomesWorld(1);w.step()
    b,c=w.agents[2],w.agents[3]
    assert not w.contact(None,c)
    assert not w.contact(b,None)
    assert not w.contact(copy.deepcopy(b),c)
    assert not w.contact(b,c)  # C still asleep until tick 2
    c.sleep_until=0; b.x=20
    assert not w.contact(b,c)
    b.x=3;w.kill(b,'test')
    assert not w.contact(b,c)
    assert 'move:hazard' not in c.learned
    assert 3 not in w.proofs


def test_proof_corruption_missing_source_and_spatial_forgery_rejected():
    w=ThreeGnomesWorld(1);w.step(2)
    for mutate in (
        lambda p:p['path'].__setitem__(0,999),
        lambda p:p['path'].__setitem__(1,3),
        lambda p:p['receipts'][0].__setitem__('sender_xy',[30,30]),
        lambda p:p['receipts'][1].__setitem__('after',-99),
        lambda p:p['root'].__setitem__('reward',-999),
    ):
        data=w.state(); mutate(data['telephone']['proofs'][3]['move:hazard'])
        with pytest.raises(ValueError):ThreeGnomesWorld.from_state(data)


def test_atomic_checkpoint_failure_and_checksum(tmp_path):
    w=ThreeGnomesWorld(1);w.step()
    path=tmp_path/'world.sqlite';save_telephone(w,path);previous=w.state()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER abort_write BEFORE INSERT ON telephone_checkpoint BEGIN SELECT RAISE(ABORT,'interrupted'); END")
    w.step()
    with pytest.raises(sqlite3.IntegrityError):save_telephone(w,path)
    assert load_probe(path).state()==previous
    with sqlite3.connect(path) as db:db.execute("UPDATE telephone_checkpoint SET sha256='wrong'")
    with pytest.raises(ValueError):load_probe(path)


def test_explicit_loader_and_writer_protect_old_formats(tmp_path):
    from gnome_fortress.communication import save_experiment, CommunicationWorld
    path=tmp_path/'old.sqlite';save_experiment(CommunicationWorld(),path);old=path.read_bytes()
    with pytest.raises(ValueError):save_telephone(ThreeGnomesWorld(),path)
    assert path.read_bytes()==old
    new=tmp_path/'new.sqlite';save_telephone(ThreeGnomesWorld(),new)
    with pytest.raises(ValueError):load_telephone(new)
    with pytest.raises(ValueError):TelephoneConfig('irrelevant')


def test_hop_limit_and_attenuation_floor_are_explicit():
    w=ThreeGnomesWorld(1);w.step(2)
    sender=w.agents[3]
    for _ in range(MAX_PATH-3):
        child=w._spawn(1 if sender.x==2 else 2,3,sender.traits,(1,2))
        assert w.contact(sender,child)
        sender=child
    assert len(w.proofs[sender.id]['move:hazard']['path'])==MAX_PATH
    assert sender.learned['move:hazard']==-1  # floor bias, not increasing certainty
    final=w._spawn(1 if sender.x==2 else 2,3,sender.traits,(1,2))
    assert not w.contact(sender,final) and w.audit[-1]['reason']=='hop_limit'
    w.validate()


def test_dead_root_can_remain_evidence_but_dead_relay_cannot_send():
    w=ThreeGnomesWorld(1);w.step()
    w.kill(w.agents[1],'test');w.agents[3].sleep_until=0
    assert w.contact(w.agents[2],w.agents[3])
    w.validate()
    interrupted=ThreeGnomesWorld(1);interrupted.step()
    interrupted.kill(interrupted.agents[2],'test');interrupted.step(2)
    assert not interrupted.latest_moves[3]['knowledge_before']
    assert interrupted.origins.get(3,{}).get('move:hazard',{}).get('social_count',0)==0
    assert interrupted.latest_moves[3]['learned'].get('move:hazard',0)==0


def test_missing_historical_source_rejected_without_delivery():
    w=ThreeGnomesWorld(1);w.step()
    w.agents[3].sleep_until=0
    w.proofs[2]['move:hazard']['path'][0]=999
    assert not w.contact(w.agents[2],w.agents[3])
    assert w.audit[-1]['reason']=='missing_source' and 3 not in w.proofs


def test_phase4a_first_transfer_math_is_preserved():
    from gnome_fortress.communication import CommunicationWorld
    w=ThreeGnomesWorld(1,'direct')
    data=World.state(w)
    data['communication']=copy.deepcopy(w.state()['communication'])
    data['communication']['config']={'condition':'social'}
    old=CommunicationWorld.from_state(data)
    assert w.contact(w.agents[1],w.agents[2])
    assert old.contact(old.agents[1],old.agents[2])
    assert w.agents==old.agents and w.origins==old.origins
    assert w.rng.getstate()==old.rng.getstate()


def test_channel_runs_from_existing_social_decision():
    w=ThreeGnomesWorld(1,'multihop')
    w.agents[1].traits['sociability']=100
    TelephoneWorld.decide(w,w.agents[1])
    assert any(e.kind=='social' and e.actor==1 and e.target==2 for e in w.events)
    assert w.messages==1 and w.proofs[2]['move:hazard']['path']==[1,2]
    assert not any(e.kind=='communication' for e in w.events)


def test_companion_inspector_readonly_and_survives_audit_eviction(tmp_path):
    from gnome_fortress.observatory import load_snapshot
    from research.phase4b_inspect import inspect_agent
    w=ThreeGnomesWorld(1);w.step(3)
    for _ in range(200): w.contact(w.agents[2],w.agents[3])
    path=tmp_path/'closed.sqlite';save_telephone(w,path)
    source=path.read_bytes();loaded=load_snapshot(path,loader=load_probe)
    snapshot=loaded.state();result=inspect_agent(loaded,3)
    proof=result['acquisition_evidence']['move:hazard']
    assert proof['received_from']==2 and proof['root_source']==1
    assert proof['source_path']==[1,2,3] and proof['firsthand_at_acquisition']==0
    assert result['recorded_movement']['terrain']=='grass'
    assert result['recorded_movement']['firsthand_hazard_before']==0
    assert loaded.state()==snapshot and path.read_bytes()==source


def test_weak_forwarded_warning_does_not_override_all_other_preferences():
    w=ThreeGnomesWorld(1);w.step(2)
    w.agents[3].visits={'1,3':1,'3,3':1}
    w.step()
    # An existing -8 revisit cost outweighs this -1 warning. No retuning allowed.
    assert w.latest_moves[3]['learned']['move:hazard']==-1
    assert w.latest_moves[3]['terrain']=='hazard'
    assert w.latest_moves[3]['firsthand_hazard_before']==0
    assert w.latest_moves[3]['knowledge_before']['move:hazard']['path']==[1,2,3]


def test_telephone_snapshots_own_their_nested_provenance():
    w=ThreeGnomesWorld(1);w.step(2)
    data=w.state();saved=copy.deepcopy(data)
    restored=ThreeGnomesWorld.from_state(data)
    restored.step();w.step()
    assert data==saved
    assert w.state()==restored.state()


def test_causal_readout_ablation_with_chain_and_b_state_held_fixed():
    informed=ThreeGnomesWorld(1);informed.step(2)
    ablated=ThreeGnomesWorld.from_state(informed.state())
    # Harness-only intervention: retain the chain, remove just its score weight.
    ablated.agents[3].learned['move:hazard']=0
    assert ablated.rng.getstate()==informed.rng.getstate()
    informed.step();ablated.step()
    assert informed.latest_moves[3]['terrain']=='grass'
    assert ablated.latest_moves[3]['terrain']=='hazard'
    assert informed.agents[2]==ablated.agents[2]
    assert informed.latest_moves[3]['knowledge_before']==ablated.latest_moves[3]['knowledge_before']
    assert informed.latest_moves[3]['firsthand_hazard_before']==ablated.latest_moves[3]['firsthand_hazard_before']==0
