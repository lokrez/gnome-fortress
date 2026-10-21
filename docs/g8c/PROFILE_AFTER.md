# G8C measured profile after

Reference c88b217. Same private original-state copy and seed-1 generated fixtures. No original-world stepping/writes. Unit timers remain during preparation; they are removed before 15 warm samples. Percentiles use linear interpolation and are descriptive, especially with only 15 warm samples. Raw outliers remain included. Independent regression/operation jobs sometimes ran concurrently on this 8-core host.

| Scale | Preparation ms: median / p95 / p99 / worst, before | After | Warm capture ms: median / p95 / p99 / worst, before | After |
|---|---:|---:|---:|---:|
| 0 | 0.02 / 0.02 / 0.02 / 0.02 | 0.08 / 0.08 / 0.08 / 0.08 | 0.47 / 0.52 / 0.53 / 0.53 | 0.50 / 0.55 / 0.57 / 0.57 |
| 26,000 | 4.51 / 4.71 / 4.79 / 4.85 | 3.35 / 3.56 / 3.65 / 3.75 | 13.54 / 15.57 / 16.79 / 17.10 | 9.30 / 11.38 / 11.54 / 11.58 |
| 428,868 | 4.45 / 4.61 / 4.70 / 90.85 | 3.26 / 3.49 / 3.61 / 1166.09 | 98.99 / 122.47 / 150.26 / 157.21 | 12.26 / 12.64 / 12.74 / 12.76 |

| Scale | Cold full-copy ms before / after | Total preparation seconds before / after | Feeder pickle ms before / after | Peak RSS GiB before / after |
|---|---:|---:|---:|---:|
| 0 | 0.7 / 1.9 | 0.00 / 0.00 | 0.0 / 0.0 | 0.02 / 0.02 |
| 26,000 | 535.9 / 530.0 | 3.24 / 2.45 | 16.7 / 17.4 | 0.47 / 0.47 |
| 428,868 | 13145.6 / 13115.3 | 52.93 / 41.08 | 307.9 / 320.0 | 11.52 / 11.52 |

Warm giant capture meets the 50/100 ms targets in these 15 samples. Preparation median/p95/p99 meet 4 ms, but the worst does **not** meet 16 ms: a 1.162-second collection was measured during an event encode. Small additional outliers are not assigned a cause without evidence. The first candidate also showed this; it is not hidden or called resolved. Cold full-copy remains seconds and is not a normal owner-loop save path while history is unprepared.

The earlier 91-ms first bind copied the event list. The new bind adopts it; retained ID metadata is initialized once. No warm historical-agent census or clean-block encode loop remains. The cProfile calls show only 376 hot agents at the giant snapshot versus 91,003 retained records before. Hot pickle/flattening is now the dominant capture work.

Copy-on-write metadata adds bounded reference chunks proportional to history. One in-flight save retains old immutable versions only while needed. Cached payload bytes and full canonical history still grow; this is not constant-memory storage. No GC policy, checksum, strict validation, format, old evidence or biology changes.

Run commands and contracts are in DESIGN.md and INTEGRITY.md. The first instrumented run timed every cached encode and overstated warm latency; it is preserved under instrumented-first, excluded only from the uninstrumented warm comparison with that explicit reason. indexed-first is the pre-headroom candidate, also preserved.
