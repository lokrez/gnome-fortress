# Profile before — generated worlds only

Starting operational implementation: `52bf735` (detached object-graph capture).
Preserved G7 thread worker is an additional reference. Seed 1, ticks 0/1,000/
3,000/10,000; three save windows per fixture. SDL-dummy runs the actual renderer.
The initial measurements were taken before the capture change; raw results are
[initial before](evidence/profile-before.json). No player save was used.

A second controlled comparison resets the generated world to the identical
fixture state before **every** repetition. It compares synchronous save, original
G7 thread worker, and pre-Saveguard whole-object pickle capture. The reference
capture is explicitly selected in the harness; SQLite algorithms and integrity
settings remain the same. [Paired reference](evidence/paired-reference.json).
This removes wall-time-dependent state drift between repetitions in the initial
benchmark. Both datasets are retained, including the initial outliers.

| Tick | Living / retained | Objective events | Sync max frame gap ms | G7 thread max frame gap ms | Detached capture max ms | Detached frame p95 / p99 ms |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 60 / 60 | 60 | 38.5 | 25.7 | 3.4 | 22.2 / 22.2 |
| 1,000 | 184 / 185 | 5,725 | 247.1 | 44.2 | 22.4 | 28.2 / 28.5 |
| 3,000 | 368 / 607 | 27,162 | 878.5 | 108.2 | 80.0 | 30.1 / 66.8 |
| 10,000 | 373 / 2017 | 107,609 | 3421.6 | 333.3 | 376.8 | 30.8 / 35.1 |

The original thread worker permits read-only rendering but stops simulation for
the full save. The synchronous reference blocks rendering too. The detached
worker runs the world during serialization/write, but its complete-tick capture
still blocks the owner thread. No stepped/torn snapshots are used.

## Measured phase attribution

The instrumented callback follows the same strict existing-file update algorithm:
validate snapshot, validate old checkpoint, assemble canonical state, JSON encode,
hash, connect/BEGIN IMMEDIATE, validate pinned old checkpoint again, write, FULL
commit, close. Phase totals are wall times, not independent CPU samples. This is
an instrumented equivalent callback rather than a claim that function-profiling
adds zero overhead. Every result is checked by the real storage reader.

| Tick | Capture median ms | State assembly median ms | JSON median ms | Old-state validation medians ms (before / transactional) | SQL begin / write / commit median ms | Writer wall / CPU median s |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 1.4 | 2.6 | 1.3 | 6.7 / 5.9 | 0.0 / 0.1 / 0.0 | 0.018 / 0.018 |
| 1,000 | 16.8 | 35.2 | 23.2 | 83.2 / 72.2 | 0.0 / 2.2 / 0.0 | 0.221 / 0.221 |
| 3,000 | 78.8 | 123.7 | 79.5 | 295.1 / 338.1 | 0.0 / 2.8 / 0.0 | 0.859 / 0.853 |
| 10,000 | 309.0 | 466.4 | 274.9 | 1099.0 / 1185.9 | 0.0 / 23.1 / 0.0 | 3.079 / 3.079 |

Remaining phase measurements (snapshot validation, hash and connection) are in
JSON. Waiting for a completed tick is zero in this harness because calls start
between completed ticks; normal engine tick duration is not counted as a save
stall. `completion_notification_seconds` measures the poll call itself, not the
entire cross-process delivery latency. Save window timing includes capture,
startup/IPC, rendering, stepping, polling and sleep. The finite short fresh-world
window undershoots the 15 t/s target because ticks are discrete and spawn startup
is included. No inference about unrestricted headless throughput is justified.

Default autosave interval: 300 simulation ticks (20 seconds at 15 t/s, 5 seconds
at 60 t/s); it is based on the snapshot's saved tick. The host was not exclusive:
the owner's existing game continued running throughout. Three samples characterize
these fixtures, not a statistical latency guarantee or a laptop benchmark.

Reproduce (temporary generated worlds; never point internal --sample at untrusted
pickle files):

```bash
.venv/bin/python -m research.saveguard_profile --capture-method reference --out /tmp/saveguard-reference.json
```
