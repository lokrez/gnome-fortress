# G8A rendering and responsiveness

Measured on the Ryzen 7 3800X development host, Python/Pygame SDL-dummy software
surfaces, 1280×720. One generated seed-1 world, advanced normally to the listed
checkpoints; 40 timed samples per operation after warm-up. No player save was
loaded. A single bounded 26,000-tick fixture tests retained-history size; this is
not a new survival study or a historical archive replay.

The old baseline is the unchanged TerrainObserver class; the new renderer uses
the same authoritative world object. Full canonical digests (including RNG) are
compared before/after all read-only graphics measurements. Existing Saveguard
code is byte-for-byte unchanged. Raw [final measurements](evidence/performance.json).

## Frame drawing cost

| Tick | Living / retained | Objective events | Old median ms | New median ms | New p95 / p99 ms | New maximum ms |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 60 / 60 | 60 | 3.12 | 6.53 | 6.90 / 7.13 | 8.91 |
| 3,000 | 368 / 607 | 27,162 | 4.45 | 7.14 | 7.43 / 7.45 | 7.48 |
| 10,000 | 373 / 2017 | 107,609 | 5.80 | 7.20 | 7.57 / 7.64 | 7.69 |
| 26,000 | 386 / 5340 | 290,808 | 8.60 | 7.33 | 8.05 / 8.19 | 8.32 |

The new UI costs more on young worlds: textured tiles and a substantially larger
map replace tiny flat markers. At 26,000 ticks it is faster than the old whole-map
renderer, which still traverses deceased individuals. This is a readability tradeoff,
not a universal speedup. Same outer window size does not mean equal rendered work:
the new viewport is 892×465 versus the old fixed map's roughly 480×320. Camera culling
also changes the visible subset deliberately; world state remains identical.

These draw-only samples are within a 16.7 ms 60 Hz budget. They do not guarantee
60 FPS when engine catch-up, checkpoint capture, actual display transport, OS load
or a cold cache is included. The host was not exclusive (the player's existing
session remained running, and some samples overlapped tests). No GPU or laptop
performance claim is made. Original [exploratory measurements](evidence/performance-initial.json)
are retained; that harness initially reported living/retained counts after its
one-tick append probe. The final run fixes counts to the actual draw tick and
records the append tick separately; no outcomes or timing outliers were removed.

## Camera, population and indexing

| Tick | Visible sprites | Sprite layout median ms | Zoom + draw max ms | Follow + draw max ms | No-append sync median ms | New events / scanned | Append update ms | Peak RSS MiB |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 45 | 0.121 | 7.02 | 10.12 | 0.0037 | 3 / 3 | 0.067 | 43.4 |
| 3,000 | 274 | 0.600 | 7.45 | 9.25 | 0.0030 | 12 / 12 | 0.139 | 86.0 |
| 10,000 | 255 | 0.584 | 7.73 | 9.09 | 0.0031 | 11 / 11 | 0.143 | 198.3 |
| 26,000 | 289 | 0.648 | 7.98 | 9.14 | 0.0030 | 15 / 15 | 0.171 | 461.9 |

No-append drawing leaves the event and land index scan counts unchanged. Only new
objective events are scanned by the append probe. One selected LifeHistory builds
on demand and then updates incrementally; there is no per-agent biography cache.
Queued intervention lists and living occupancy refresh per tick/request changes,
not by rescanning historical events every frame. Cached art/text use bounded LRU
sizes; only visible terrain/gnomes are drawn, and at most nine sprites per shared
tile plus a real occupancy count. The selected individual is included and drawn
last; repeated-click cycling reaches other living occupants.

RSS is a cumulative per-process high-water mark including the full retained world,
indexes, sprite caches and full-state digest verification. It is not a graphics-only
allocation count or a long-term memory-leak guarantee. The follow microbenchmark
uses a static completed-tick world to isolate rendering cost; moving-target
functionality is separately demonstrated by the actual 30-tick follow trace.

## Autosave integration

A scripted real Pygame run at tick 600 used a controlled 0.5-second delay in the
normal detached writer. It continued stepping and rendering while SAVING, then
Escape drained the snapshot and committed the latest live state exactly.

Measured capture/start: **16.2 ms**; maximum serviced frame gap **31.1 ms** in this short scenario. Live ticks **600 → 611**, with older snapshot tick **600**. Shutdown drain waited **0.576 s**; final synchronous save took **0.157 s**.

[Trace and capture metadata](evidence/captures.json). This small fixture does not
supersede Saveguard's larger-world measurements: at 10,000 ticks, its documented
capture was about 156 ms median / 226 ms worst. G8A does not fix or conceal that
remaining main-thread capture hitch. No simulation time is added for animations,
and changing zoom/pan/tabs does not itself trigger autosaves.

## Reproduction

```bash
.venv/bin/python -m research.g8a_evidence --out /tmp/g8a-captures
.venv/bin/python -m research.g8a_evidence --bench --out /tmp/g8a-performance
```

Both commands create isolated generated worlds. No default/player checkpoint is
opened. Captures are actual Pygame surfaces. Human smoothness/readability feedback
is still required; SDL-dummy timings cannot establish enjoyment or 4K display latency.
