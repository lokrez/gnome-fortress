"""Fixed, bounded G1 comparison: genuine resource accounting and observed outcomes."""
import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import time

from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game,save_game


def metrics(w,condition):
    food=sum(c.food for row in w.cells for c in row)
    living=w.living()
    return dict(condition=condition,tick=w.tick,living=len(living),born=len(w.agents),
        deaths=len(w.agents)-len(living),food=food,
        hunger_total=sum(a.hunger for a in living),
        eats=sum(m.action=='eat' for a in w.agents.values() for m in a.memories),
        regenerated=sum(p.totals['regenerated'] for p in w.interventions),
        delta_from_local_normal=sum(p.totals['delta'] for p in w.interventions),digest=w.digest())


def run(output):
    if output.exists():raise ValueError('Use a new output directory; preserving prior demonstrations')
    output.mkdir(parents=True)
    started=time.perf_counter();worlds={c:GameWorld(1) for c in ('observation','rain','drought')}
    rows=[];active_reload={}
    for w in worlds.values():w.step(20)
    assert all(World.state(w)==World.state(worlds['observation']) for w in worlds.values())
    for condition,w in worlds.items():
        rows.append(metrics(w,condition))
        if condition!='observation':w.request(condition,24,16,radius=8,duration=150)
    with tempfile.TemporaryDirectory() as directory:
        for boundary in (21,30,50,100,170,171,200,300):
            for condition,w in worlds.items():
                w.step(boundary-w.tick);w.validate();rows.append(metrics(w,condition))
                if boundary==50:
                    path=Path(directory)/(condition+'.g1.sqlite');save_game(w,path)
                    active_reload[condition]=load_game(path)
        for condition,w in worlds.items():
            loaded=active_reload[condition];loaded.step(250)
            assert loaded.state()==w.state()
    # Independently replay the complete recorded request sequence from the same seed.
    for condition,w in worlds.items():
        replica=GameWorld(w.seed)
        for p in w.interventions:
            replica.step(p.requested_tick-replica.tick)
            replica.request(p.kind,p.x,p.y,p.radius,p.duration)
        replica.step(w.tick-replica.tick)
        assert replica.state()==w.state()
    with (output/'comparison.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    result=dict(seed=1,ticks=300,request_tick=20,activation_tick=21,expires_tick=171,
        center=[24,16],radius=8,duration=150,
        final={c:metrics(w,c) for c,w in worlds.items()},
        interventions={c:[asdict(p) for p in w.interventions] for c,w in worlds.items()},
        deaths={c:[dict(tick=e.tick,agent=e.actor,**e.detail) for e in w.events if e.kind=='death'] for c,w in worlds.items()},
        pre_intervention_exact=True,deterministic_replays=3,active_reload_continuations=3,
        seconds=time.perf_counter()-started)
    (output/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    run(p.parse_args().output)
