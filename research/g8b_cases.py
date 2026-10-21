"""Predeclared natural observation windows; no fixture changes or forced actions."""
import json
from pathlib import Path
from collections import Counter
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.decision_observation import DecisionObservation
from gnome_fortress.terrain_checkpoint import capture_snapshot

OUT=Path('docs/g8b/evidence');OUT.mkdir(parents=True,exist_ok=True)
TEMP=Path('/tmp/gnome-g8b-natural-cases');TEMP.mkdir(exist_ok=True)


def main():
    cases={};runs=[]
    # Fixed seeds, founder IDs and horizons before inspecting outcomes.
    windows=[(seed,identity,600) for seed in (1,42) for identity in range(1,9)]
    windows.append((1,1,3100))
    for seed,identity,horizon in windows:
        w=TerrainWorld(seed);o=DecisionObservation();o.start(w,identity)
        counts=Counter();learning=Counter();last_tick=0;individual_saved=False
        for _ in range(horizon):
            w.step()
            if not o.records:continue
            r=o.records[-1]
            if r['tick']==last_tick:continue
            last_tick=r['tick'];d=r['decision'];tags=[]
            if d:
                counts[d['action']]+=1
                if not individual_saved and d['action'] in ('eat','drink','socialize','reproduce'):
                    tags.append(f'individual-{seed}-{identity}');individual_saved=True
                for change in d['learning']:
                    if change['previous']!=change['current']:
                        learning[change['key']]+=1;tags.append('learning')
                if d['action'] in ('eat','drink','sleep','socialize','reproduce'):tags.append(d['action'])
                if d['movement'] and d['movement']['candidates']:
                    tags.append('movement')
                    if any(c['terrain']=='hazard' for c in d['movement']['candidates']):tags.append('hazard_candidates')
                    if any(c['learned_contribution']!=0 for c in d['movement']['candidates']):tags.append('learned_readout')
                if any(e['kind']=='hazard' for e in d['events']):tags.append('hazard_experience')
            else:counts['no_slot']+=1;tags.append('no_slot')
            if not w.agents[identity].alive:tags.append('death')
            for tag in tags:
                if tag not in cases:
                    cases[tag]=dict(seed=seed,identity=identity,traits=dict(w.agents[identity].traits),record=r)
                    (TEMP/f'{tag}.pickle').write_bytes(capture_snapshot(w))
                    (OUT/f'case-{tag}.json').write_text(json.dumps(cases[tag],indent=2)+'\n')
            if not o.enabled:break
        a=w.agents[identity]
        runs.append(dict(seed=seed,identity=identity,horizon=horizon,observed_until=last_tick,
                         counts=dict(counts),learning_changes=dict(learning),alive=a.alive,
                         died=a.died,death_cause=a.death_cause,children=a.children,
                         traits=dict(a.traits),final_learned=dict(a.learned),
                         retained_trace=len(o.records),memory_length=len(a.memories),error=o.error))
        print(seed,identity,horizon,last_tick,dict(counts),flush=True)
    (OUT/'natural-cases.json').write_text(json.dumps(dict(protocol=dict(seeds=[1,42],founders=list(range(1,9)),
        horizon=600,extended=dict(seed=1,identity=1,horizon=3100)),cases=cases,runs=runs),indent=2)+'\n')


if __name__=='__main__':main()
