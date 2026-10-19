import json
import time

from gnome_fortress.engine import World
from gnome_fortress.storage import load, save


def test_twenty_thousand_ticks(tmp_path):
    start = time.monotonic()
    w = World(2026)
    for _ in range(40):
        w.step(500)
        w.validate()
        if w.tick % 5000 == 0:
            print(f"long-run progress: tick={w.tick}, living={len(w.living())}, born={len(w.agents)}", flush=True)
    path = tmp_path / "long.sqlite"
    save(w, path)
    restored = load(path)
    assert restored.digest() == w.digest()
    w.step(100)
    restored.step(100)
    assert w.digest() == restored.digest()
    w.validate()
    assert w.tick == 20100
    assert len(w.agents) > 60
    assert any(e.kind == "death" for e in w.events)
    assert any(e.kind == "reproduce" for e in w.events)
    print("long-run result:", json.dumps({**w.summary(), "digest": w.digest(),
                                           "seconds": round(time.monotonic()-start, 3)}))
