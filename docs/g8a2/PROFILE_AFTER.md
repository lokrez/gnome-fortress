# After: detached mutable state + prepared history

Production `TerrainCheckpointWorker.start` captures a frozen `PreparedPayload`: current mutable bytes plus immutable history byte references. Historical byte copying/IPC occurs in the pool feeder; full reconstruction and validated SQLite storage occur in the spawned process. No background code reads the live World.

Three generated seed-1 horizons, seven warmed captures each. The accepted reference and optimized decoded states/RNG agree. Cold means an immediate capture with no preparation; warm means preparation has caught up. Measurements include concurrent development/test processes and the owner's untouched older game, not exclusive hardware.

| Tick | Events | Cold ms | Warm median ms | Warm maximum ms | Mutable hot MiB | Complete IPC MiB | Preparation total s | Prep median / max ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 3,000 | 27,162 | 36.94 | 9.03 | 10.30 | 0.84 | 2.62 | 0.22 | 4.10 / 12.40 |
| 10,000 | 107,609 | 191.00 | 12.47 | 13.06 | 0.84 | 9.45 | 1.12 | 4.44 / 5.72 |
| 26,000 | 290,808 | 500.66 | 17.10 | 17.34 | 0.84 | 25.21 | 3.28 | 4.47 / 108.26 |

The 26k warmed capture is about 17 ms versus roughly 475 ms reference capture, with the same complete history. Current mutable data stays around 0.84 MiB across these horizons; agent ordering and segment references still grow with retained history. No constant-time or infinite-memory claim is made. The standalone `capture` bytes convenience method also encodes the full envelope; that extra historical-byte copy is intentionally excluded from production owner-thread latency because it runs in the feeder there.

Cold capture is **not fixed**: at 26k it remains about 501 ms. An immediate manual save or invalidated cache can take the safe complete path. Preparation is distributed with a 4 ms soft budget; these back-to-back cold probes include a 108 ms GC/allocation outlier. We did not disable garbage collection or discard that outlier. Ordinary ongoing work is much lower once preparation catches up.

## Worker and memory

In the separate 26k worker probe, capture/start took **14.63 ms**; total completion **9.89 s**. Reconstruction took **0.965 s**.

| Worker phase | Seconds |
|---|---:|
| snapshot_validation | 0.079143 |
| previous_checkpoint_validation | 3.100933 |
| canonical_state_assembly | 1.348814 |
| json_serialization | 0.737837 |
| checksum | 0.053624 |
| sqlite_connect | 0.000115 |
| sqlite_begin | 0.000016 |
| transactional_previous_validation | 3.033566 |
| sqlite_payload_write | 0.065810 |
| sqlite_commit_fsync | 0.000022 |

Fresh-process resident memory was **354.4 MiB** before preparation, **379.7 MiB** after preparation, and **385.1 MiB** after twenty captures. Event blocks / dead records remained **2271 / 4954** across those captures. Cached bytes at 26k are about **24.3 MiB**, plus mutation metadata. Allocator reuse means RSS differences are not exact object-allocation accounting.

Writer peak RSS was **1219.3 MiB**, largely full prior-state validation and JSON graphs. Multi-horizon harness high-water marks approach 1 GiB during repeated whole-state/digest validation; those are not steady cache residency. There is one cache representation per retained history, not one per checkpoint generation. Memory still grows linearly with the canonical history.

The unchanged strict writer validates the previous checkpoint twice, accounting for much of its ~9 seconds. That happens off the gameplay thread. Accelerated play can outpace disk checkpoint completion; the existing single-active-save/coalescing policy remains. This milestone does not promise every 300-tick interval is durably committed at arbitrary accelerated speed. Final exit still drains and writes the latest state synchronously; wait for the terminal prompt.

## Steady simulation throughput

Matched generated worlds advance 600 ticks from tick 26,000. Four preparation calls per tick approximate 60 display frames / 15 simulation ticks per second. Reference **2.277 s**, optimized **2.378 s**: **4.42%** additional elapsed time; preparation accounts for **0.110 s**. Final canonical state/RNG is identical. Cold preparation is excluded here and reported separately above. This is a short hardware probe, not a universal throughput guarantee.

The first implementation cost about 20% extra time because every birth rescanned all retained agents. The final version uses monotonic new IDs and living-set differences, while capture still checks cached dead-object identities. Earlier throughput files remain evidence of the rejected implementation cost.

## Actual desktop frames

See `operation.json` for every frame, preparation and save. Three completed background checkpoints (two automatic, one explicit retry), one injected failed automatic write, live navigation, a real Rain request, final save and reload continuation were executed using an isolated mature checkpoint and the real X11 Pygame build. The report summarizes those raw traces, including cold startup outliers; it does not equate capture timing with full frame latency. Human smoothness testing remains pending.

The desktop frame summary records an overall maximum of 135.92 ms during cold startup/index rebinding (no save pending), warm maximum 83.58 ms, and overall p99 26.27 ms. Scripted controls and a PNG capture occur in the first pending-save frame, so this is conservative operational evidence rather than a draw-only timing. All samples remain in the raw trace.
