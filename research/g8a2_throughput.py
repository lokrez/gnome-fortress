"""Warm steady-state preparation overhead; matched generated mature worlds."""
import json,pickle,time
from pathlib import Path
from gnome_fortress.chronicle import Chronicle


def main():
    source=Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes();a=pickle.loads(source);b=pickle.loads(source);c=Chronicle()
    while True:
        c.prepare(b)
        if len(b.events)-c.prepared<128 and not c.dead_queue:break
    rows=[]
    for start in range(0,600,100):
        t=time.perf_counter();a.step(100);reference=time.perf_counter()-t
        prep=0;t=time.perf_counter()
        for _ in range(100):
            b.step()
            for frame in range(4):prep+=c.prepare(b)
        optimized=time.perf_counter()-t
        rows.append(dict(first_tick=26000+start,reference_seconds=reference,optimized_seconds=optimized,preparation_seconds=prep))
    assert a.state()==b.state()
    Path('docs/g8a2/evidence/throughput.json').write_text(json.dumps(dict(rows=rows,exact=True,final_digest=a.digest()),indent=2)+'\n')


if __name__=='__main__':main()
