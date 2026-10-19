"""Complete logical fingerprints and exact field comparison without giant copies."""
from dataclasses import fields
import hashlib
from gnome_fortress.model import Agent
from gnome_fortress.storage import add_hash,header,record,event_rows


def fingerprint(w):
    h=hashlib.sha256();add_hash(h,header(w))
    for row in w.cells:add_hash(h,[(c.terrain,c.food) for c in row])
    for a in w.agents.values():add_hash(h,(a.id,record(a)[-1]))
    for e in event_rows(w):add_hash(h,e)
    return h.hexdigest()


def assert_exact(a,b):
    assert header(a)==header(b),'header/RNG mismatch'
    assert [[(c.terrain,c.food) for c in r] for r in a.cells]==[[(c.terrain,c.food) for c in r] for r in b.cells]
    assert list(a.agents)==list(b.agents),'identity/order mismatch'
    names=tuple(f.name for f in fields(Agent) if f.name!='memories')
    for identity,left in a.agents.items():
        right=b.agents[identity]
        assert all(getattr(left,k)==getattr(right,k) for k in names),f'agent mismatch {identity}'
        assert [vars(m) for m in left.memories]==[vars(m) for m in right.memories],f'memory mismatch {identity}'
    assert len(a.events)==len(b.events),'event count mismatch'
    for i,(left,right) in enumerate(zip(a.events,b.events)):
        assert vars(left)==vars(right),f'event mismatch {i}'
