"""Supplement bounded provenance evidence without changing fixtures or cohort sizes."""
import argparse
import copy
import json
from pathlib import Path

from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld
from research.phase4b_experiment import ThreeGnomesWorld


def collect(directory):
    original=[]
    for seed in range(1,65):
        w=ThreeGnomesWorld(seed);w.step(2)
        proof=copy.deepcopy(w.proofs[3]['move:hazard'])
        assert proof['path']==[1,2,3]
        assert all(r['firsthand_before']==0 for r in proof['receipts'])
        original.append(dict(seed=seed,proof=proof,acquired=w.agents[3].learned['move:hazard'],
                             origin=copy.deepcopy(w.origins[3]['move:hazard'])))
    (directory/'original-provenance.json').write_text(json.dumps(original,indent=2)+'\n')
    pilots=json.loads((directory/'pilot.json').read_text());evidence=[]
    # Select from the already bounded diagnostic examples, never add meetings.
    for saved in pilots:
        examples=[e for e in saved['examples'] if e['depth']>1]
        if not examples:continue
        ids={e['agent'] for e in examples};proofs={}
        w=TelephoneWorld(saved['seed'],TelephoneConfig(saved['condition']))
        contact=w.contact
        def capture(sender,recipient):
            accepted=contact(sender,recipient)
            if accepted and recipient.id in ids:
                proofs[recipient.id]=copy.deepcopy(w.proofs[recipient.id]['move:hazard'])
            return accepted
        w.contact=capture;w.step(saved['ticks']);del w.contact
        assert w.digest()==saved['digest']
        for example in examples:
            proof=proofs[example['agent']]
            assert len(proof['path'])-1==example['depth']
            assert all(r['firsthand_before']==0 for r in proof['receipts'])
            root=proof['root']
            assert any(e.kind=='hazard' and e.actor==root['agent'] and e.tick==root['tick']
                       and e.detail['damage']==-root['reward']//3 for e in w.events)
            evidence.append(dict(seed=saved['seed'],condition=saved['condition'],proof=proof,decision=example))
    (directory/'natural-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(original_proofs=len(original),bounded_forwarded_examples=len(evidence))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    collect(p.parse_args().directory)
