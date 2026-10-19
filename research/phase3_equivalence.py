"""Exact mature-state oracle checks; never write historical checkpoint files."""
import hashlib,json
from pathlib import Path
from gnome_fortress.storage import load
from research.phase3.reference.storage import load as reference_load
from research.phase3_check import assert_exact,fingerprint

ROOT=Path('research/phase3')


def main():
    outputs=[]
    sources=[Path('research/phase1/data/seed-01/final.sqlite')]
    sources += [Path(f'research/phase2/data/endurance/seed-{s:02d}/final.sqlite') for s in (1,2,3)]
    for source in sources:
        a,b=load(source),reference_load(source)
        start=a.tick;checks=[]
        for offset in (0,1,50,200):
            a.step(start+offset-a.tick);b.step(start+offset-b.tick)
            a.validate();b.validate();assert_exact(a,b)
            checks.append(dict(tick=a.tick,exact_agent_fields=True,exact_memories=True,
                               exact_rng=True,exact_events=True,exact_cells_and_scheduler=True))
        outputs.append(dict(source=str(source),boundaries=checks,final_fingerprint=fingerprint(a)))
        print('EXACT',source,','.join(str(c['tick']) for c in checks),flush=True)
        del a,b
    (ROOT/'equivalence.json').write_text(json.dumps(dict(reference_commit='5efc9b1bfdd8d49a13aefd4e9256e6c1e87c024f',
        fingerprint_note='Complete logical streaming SHA-256; different encoding from World.digest',
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),runs=outputs),indent=2)+'\n')

if __name__=='__main__':main()
