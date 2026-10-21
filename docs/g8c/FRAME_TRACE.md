# Actual Pygame frame trace

Real LivingObserver/owner loop and spawned Saveguard writer. SDL dummy, 1280×720. No human smoothness approval is claimed. Private generated/copy worlds only. All frame gaps are retained, including startup, automated control/screenshot work, GC and feeder interference. Percentiles are observed distributions, not guarantees.

| Session | Frames | Frame gap ms: median / p95 / p99 / worst | Capture ms: median / p95 / p99 / worst |
|---|---:|---:|---:|
| 26k warm | 537 | 17.04 / 26.64 / 38.76 / 110.64 | 11.63 / 13.35 / 13.55 / 13.60 |
| 26k cold preparing | 1357 | 19.35 / 27.95 / 33.83 / 222.76 | 12.95 / 16.11 / 16.55 / 16.66 |
| giant warm | 2667 | 16.55 / 22.85 / 27.98 / 423.99 | 15.27 / 16.41 / 16.51 / 16.54 |
| 26k repeated, drain timed | 550 | 17.67 / 26.61 / 41.87 / 113.08 | 11.77 / 14.54 / 14.83 / 14.90 |

Per-frame simulation/render times, preparation progress, GC thread/context, owner capture times, pool feeder serialization and save/reconstruction/completion metrics are in the raw JSON. Input scripts exercised selection, follow, Advisor, Decisions, Land and a genuine Rain request while the writer was pending. The 26k sessions also injected a controlled child-save failure and explicit retry.

The cold 26k session starts unprepared: the manual request remains pending while the actual world advances; the loop does not call the full cold fallback. Its first saved tick is later than the request tick and is reported truthfully. Warm sessions explicitly prepare before opening the viewport; their warmup costs are recorded, not concealed as gameplay.

At giant scale the first manual snapshot is captured while paused at 428,868, then the world resumes and receives Rain before the worker finishes. The first full saved JSON SHA must equal the private original checksum. Exit drains any newly pending writer and synchronously saves the latest tick; reload and 20 further ticks are checked against uninterrupted state.

A pool feeder runs in another thread but may hold the GIL while pickling hundreds of MB. Its measured serialization is not owner detach time. GC and feeder stalls remain potential visible hitches, even with fast warm capture. Do not equate SDL dummy frame timings with human-perceived smoothness. Giant final owner save is timed separately; earlier runs did not separately time pool drain. The later repeated 26k trace records it explicitly.
