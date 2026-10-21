# G8A.1 rendering measurements

AMD Ryzen 7 3800X, Python 3.14.4, pygame-ce 2.5.8, SDL-dummy software surfaces. Thirty warmed samples per operation. Same generated seed-1 world object for both renderers, accepted G8A art/view source loaded directly from commit `2636861062eb8762c55335943379613ed457a5b1`. No player checkpoint was read. Full world/RNG digest assertions surround read-only measurements. The host is not exclusive, and short focused checks overlapped a few samples; maxima are retained rather than filtered.

A bounded natural fixture reaches tick 26,000 with 386 living, 5,340 retained individuals and 290,808 objective events. This is a rendering fixture, not a new population study. Initial and optimized runs are both retained. Final static grain/transition-wording cleanup changes artwork, not the warmed draw/cache algorithm measured here. Final artwork is covered by the targeted and fast regression logs.

## Steady drawing

| Tick | Window | Accepted G8A median ms | Folklore median ms | Folklore p95 ms | Folklore worst ms | Process peak MiB |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 800×600 | 1.87 | 4.13 | 4.78 | 4.85 | 43.2 |
| 0 | 1280×720 | 6.16 | 8.47 | 9.29 | 10.40 | 49.0 |
| 0 | 1920×1080 | 10.35 | 12.36 | 12.90 | 13.44 | 58.2 |
| 0 | 3840×2160 | 6.53 | 8.63 | 9.23 | 12.48 | 109.8 |
| 26,000 | 800×600 | 2.29 | 4.26 | 4.43 | 4.76 | 523.6 |
| 26,000 | 1280×720 | 6.83 | 9.14 | 9.41 | 9.51 | 523.8 |
| 26,000 | 1920×1080 | 10.96 | 13.58 | 14.37 | 15.14 | 523.8 |
| 26,000 | 3840×2160 | 9.55 | 11.26 | 12.03 | 13.64 | 524.0 |

These are drawing times, not measured display FPS. The art pass costs roughly 2–3 ms at 1280×720 versus G8A. Different toolbar wrapping and initial viewport sizes mean the two versions do not always rasterize equal areas. At 1920×1080, the initial view renders more small tiles than the initial 4K zoom, so timings need not grow monotonically with window size. Actual compositor transport, engine updates and save capture are additional work. No claim about laptop performance or enjoyment follows from these numbers.

## Profile-driven change

The initial implementation used an alpha-blended edge/history layer on each terrain tile every frame. At 4K it measured 17.27 ms median in the young world and 19.46 ms in the mature world. Profiling found map blits dominant (44,850 blits across 30 frames, 0.381 seconds cumulative). Baking these marks into an opaque cached terrain surface reduced that to 23,850 blits / 0.109 seconds in the same 30-frame profiler. Final 4K medians are 8.63 / 11.26 ms. The per-tile composition equality test verifies pixel equivalence. No world state is cached into these surfaces.

[Initial measurements](evidence/performance-initial.json), [final measurements](evidence/performance.json), [before profile](evidence/profile-before.txt), [after profile](evidence/profile-after.txt). Profiling instrumentation overhead differs from ordinary draw timing. No outlier was discarded.

## Interaction and caches

| Tick | Window | Sprite layout median ms | Zoom+draw worst ms | Follow+draw worst ms | No-append index sync median ms | Startup+first draw ms |
|---:|---|---:|---:|---:|---:|---:|
| 0 | 800×600 | 0.074 | 7.29 | 7.23 | 0.0043 | 37.6 |
| 0 | 1280×720 | 0.120 | 9.92 | 12.81 | 0.0029 | 40.7 |
| 0 | 1920×1080 | 0.063 | 12.21 | 12.32 | 0.0029 | 25.7 |
| 0 | 3840×2160 | 0.062 | 18.24 | 16.11 | 0.0040 | 76.7 |
| 26,000 | 800×600 | 0.414 | 7.51 | 7.15 | 0.0029 | 66.1 |
| 26,000 | 1280×720 | 0.623 | 9.16 | 10.21 | 0.0030 | 72.0 |
| 26,000 | 1920×1080 | 0.427 | 15.11 | 7.75 | 0.0037 | 71.9 |
| 26,000 | 3840×2160 | 0.370 | 17.19 | 14.33 | 0.0030 | 88.6 |

Startup includes display setup, initial disposable history indexes and first art generation; it is not a pure cache allocation measurement. Zoom samples include first-use scaled assets. Follow samples isolate drawing a static completed-tick state; moving follow is exercised separately in the running captures and existing tests. No-append measurements assert the historical index scan counters do not grow. They do not rescan 290,808 events per frame.

The separate synthetic dense fixture puts 60 founders on one tile: nine drawn sprites plus actual count/cycling, median 1.38 ms / maximum 1.67 ms. It is explicitly synthetic and is not used to claim naturally formed groups. The ordinary mature fixture supplies hundreds of living gnomes and thousands of deceased records.

Final caches after mixed sizes/zooms: 48 native gnomes, 278 scaled sprite/mask pairs, 40 native terrain surfaces, 276 scaled tiles, 1,024 composed tiles (bounded LRU full), 361 boundary/history layers, eight glyphs and seven panel sizes. Exact hit/miss counts and capacities are in raw JSON. Composed artwork recorded about 719,000 cache hits versus 3,656 misses across the mixed workload.

At the camera ceiling of 96px, the composed-terrain cache has a conservative surface-pixel bound of 36 MiB; the scaled terrain cache 18 MiB, edge/history layers 36 MiB. Actual mixed-size occupancy is lower. Sprite/mask, paper panel, text, SDL screen and allocator allocations are additional. The panel cache retains at most 64 dimensions, so repeated resizing can retain more paper surfaces than an ordinary session. These are bounds/observed counts, not a graphics-only RSS measurement. Peak RSS in the table is cumulative and includes both reference/current renderers, caches, full retained worlds, indexes and temporary canonical digest graphs. It must not be interpreted as the new art alone using 524 MiB, nor as a leak test.

## Detached saves and remaining hitch

The actual X11 running-build evidence shows ticks advancing during a controlled 0.5-second delayed detached writer, then exact save/load under a temporary ownership session. A second generated mature-world operation uses the normal writer at tick 26,000:

- Snapshot capture/start: **506.0 ms** on the owner thread.
- **60** drawn/stepped frames while the writer future was unfinished; world advanced **26,000 → 26,060**.
- Step+draw median **19.77 ms**, worst **53.03 ms** during that operation. This includes engine work and concurrent writer CPU.
- Saved snapshot was at tick 26,000; loading it and replaying the 60 ticks matched the live world's full state exactly.
- Three separate snapshot-only probes: median **466.6 ms**, worst **593.0 ms**.

The half-second capture stall at this large retained history is real. It is the existing Saveguard detached-snapshot cost, not fixed or hidden by the art pass. Drawing and simulation continue after capture while validation/writing occurs in the child. UI-only actions do not request autosaves. No ownership, write transaction, retry, final-drain or recovery logic changed.

## Reproduce

```bash
.venv/bin/python -m research.g8a1_evidence --bench --out /tmp/g8a1-performance
```

Captures use actual X11 separately; a borderless evidence window provides exact 3840×2160 because the desktop constrains decorated windows. Four actual sizes and the constrained-window fallback are tested. A human smoothness/accessibility check is still required.
