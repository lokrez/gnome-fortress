"""Bounded passive pilot measurements; no prescribed meetings or behavioral changes."""
from collections import Counter
from dataclasses import asdict
import copy
import time

from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld
from research.phase4c_tools import (ChoiceObserver, MixedOrigin, best, coupled_choice,
                                   digest, pure_social, scores)

SEEDS=(1,2,3)
CONDITIONS=('individual','direct','multihop','masked')
TICKS=300


class PilotObserver:
    def __init__(self,world):
        self.world=world;self.counts=Counter();self.usage={};self.examples=[]
        self.base_contact=world.contact

    def contact(self,sender,recipient):
        accepted=self.base_contact(sender,recipient)
        if accepted:
            proof=self.world.proofs[recipient.id]['move:hazard']
            depth=len(proof['path'])-1
            self.counts['direct_deliveries' if depth==1 else 'multihop_deliveries']+=1
            self.counts['opaque_deliveries' if proof['masked'] else 'content_deliveries']+=1
            self.usage[recipient.id]=dict(id=recipient.id,tick=self.world.tick,depth=depth,
                root=copy.deepcopy(proof['root']),masked=proof['masked'],
                acquired=recipient.learned.get('move:hazard',0),moves=0,clean_moves=0,
                mixed_moves=0,applicable_moves=0,ranking_changed=0,decision_changed=0,hazard_avoided=0)
        return accepted

    def choose(self,agent,candidates,options,rng):
        self.counts['all_movement_decisions']+=1
        usage=self.usage.get(agent.id)
        if not usage:return rng.choice(options)
        usage['moves']+=1
        if usage['masked']:return rng.choice(options)
        try:clean=pure_social(self.world,agent)
        except MixedOrigin:
            usage['mixed_moves']+=1;self.counts['mixed_excluded_moves']+=1
            return rng.choice(options)
        if not clean:return rng.choice(options)
        usage['clean_moves']+=1;self.counts['clean_social_moves']+=1
        before_rng=rng.getstate()
        masked=scores(self.world,agent,ablate=True)
        # Passive score probing must not disturb the actual generator.
        assert rng.getstate()==before_rng
        counterpart=coupled_choice(masked,before_rng)
        chosen=rng.choice(options)
        hazard=any(self.world.cell(x,y).terrain=='hazard' for _,x,y in candidates)
        safe=any(self.world.cell(x,y).terrain not in ('hazard','rock','water') for _,x,y in candidates)
        applicable=hazard and safe
        ranked={(x,y) for _,x,y in best(candidates)}!={(x,y) for _,x,y in best(masked)}
        changed=counterpart is not None and chosen[1:]!=counterpart[1:]
        avoided=counterpart is not None and self.world.cell(counterpart[1],counterpart[2]).terrain=='hazard' and self.world.cell(chosen[1],chosen[2]).terrain!='hazard'
        for field,value in [('applicable_moves',applicable),('ranking_changed',ranked),('decision_changed',changed),('hazard_avoided',avoided)]:
            usage[field]+=int(value);self.counts[field]+=int(value)
        if changed and len(self.examples)<8:
            self.examples.append(dict(tick=self.world.tick,agent=agent.id,depth=usage['depth'],
                firsthand_before=0,candidates=candidates,ablated_candidates=masked,
                actual=chosen,counterfactual=counterpart,hazard_avoided=avoided,
                rng_before=digest(before_rng)))
        return chosen

    def finish(self):
        records=[]
        for identity,usage in sorted(self.usage.items()):
            a=self.world.agents[identity]
            receipt_present=any(m.action=='hear' and m.tick==usage['tick'] for m in a.memories)
            verified=self.world.origins.get(identity,{}).get('move:hazard',{}).get('firsthand_count',0)>0
            record=dict(usage,alive=a.alive,episode_evicted=not receipt_present,
                firsthand_by_end=verified,association_retained='move:hazard' in a.learned,
                current_proof_is_firsthand=len(self.world.proofs[identity]['move:hazard']['path'])==1)
            records.append(record)
        meaningful=[r for r in records if not r['masked']]
        return dict(counts=dict(self.counts),recipients=records,examples=self.examples,
            content_recipients=len(meaningful),unused_no_applicable=sum(r['applicable_moves']==0 for r in meaningful),
            no_movement=sum(r['moves']==0 for r in meaningful),
            used_without_changed_choice=sum(r['applicable_moves']>0 and r['decision_changed']==0 for r in meaningful),
            changed_recipients=sum(r['decision_changed']>0 for r in meaningful),
            not_personally_verified=sum(not r['firsthand_by_end'] for r in meaningful),
            episode_evicted=sum(r['episode_evicted'] for r in meaningful),
            association_missing=sum(not r['association_retained'] for r in meaningful),
            mixed_recipients=sum(r['mixed_moves']>0 for r in meaningful))


def run_world(seed,condition,ticks=TICKS):
    w=TelephoneWorld(seed,TelephoneConfig(condition));observer=PilotObserver(w)
    original_rng=w.rng
    w.contact=observer.contact
    w.rng=ChoiceObserver(original_rng,observer.choose)
    started=time.perf_counter();w.step(ticks);seconds=time.perf_counter()-started
    w.rng=original_rng;del w.contact
    w.validate()
    metrics=observer.finish()
    metrics.update(seed=seed,condition=condition,ticks=ticks,living=len(w.living()),
        opportunities=w.opportunities,attempts=w.contact_attempts,messages=w.messages,
        rejections=dict(w.rejections),genuine_social_events=sum(e.kind=='social' for e in w.events),
        digest=w.digest(),slots=len(w.slots))
    return metrics,w,seconds
