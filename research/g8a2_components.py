"""Non-additive isolated payload-component probes on generated reference fixtures."""
import json,pickle,time
from pathlib import Path


def probe(build):
    samples=[]
    for _ in range(3):
        t=time.perf_counter();data=build();built=time.perf_counter();blob=pickle.dumps(data,protocol=5);end=time.perf_counter()
        samples.append(dict(build_ms=(built-t)*1000,pickle_ms=(end-built)*1000,bytes=len(blob)))
    return samples


def main():
    rows=[]
    for tick in (3000,10000,26000):
        w=pickle.loads(Path(f'/tmp/gnome-g8a2-generated-fixtures/{tick}.pickle').read_bytes())
        row=dict(tick=tick,episodes=probe(lambda:{i:[vars(m) for m in a.memories] for i,a in w.agents.items()}),
            relationships=probe(lambda:{i:a.relationships for i,a in w.agents.items()}),
            learned=probe(lambda:{i:a.learned for i,a in w.agents.items()}),visits=probe(lambda:{i:a.visits for i,a in w.agents.items()}),
            live_agents=probe(lambda:{i:{**vars(a),'memories':[vars(m) for m in a.memories]} for i,a in w.agents.items() if a.alive}),
            dead_agents=probe(lambda:{i:{**vars(a),'memories':[vars(m) for m in a.memories]} for i,a in w.agents.items() if not a.alive}),
            scheduler=probe(lambda:dict(slots=w.slots,cursor=w.cursor,next_id=w.next_id,rng=w.rng.getstate())))
        # A separate, explicitly controlled five-power microfixture for ledger cost.
        for kind in ('rain','drought','rupture','rewild','wellspring'):w.request(kind,5,5)
        w.step(10);row['five_power_records']=probe(lambda:[vars(p) for p in w.interventions])
        rows.append(row)
    Path('docs/g8a2/evidence/components.json').write_text(json.dumps(dict(non_additive=True,rows=rows),indent=2)+'\n')


if __name__=='__main__':main()
