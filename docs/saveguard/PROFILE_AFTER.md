# Profile after — bounded coherent capture

Raw final comparison: [paired after](evidence/paired-after.json); same seed,
fixtures and three repetitions as [paired reference](evidence/paired-reference.json).
Each repetition resets to the identical fixture before timing its save window.
Earlier exploratory timings remain in [initial after](evidence/profile-after.json).
No unsuccessful/outlying timing was removed.

| Tick | Capture before median / max ms | Capture after median / max ms | Frame max before / after ms | After frame p95 / p99 ms | Save-window ticks/s before / after |
|---:|---:|---:|---:|---:|---:|
| 0 | 1.4 / 3.4 | 0.8 / 2.2 | 27.1 / 28.4 | 23.2 / 23.2 | 5.14 / 5.82 |
| 1,000 | 16.8 / 22.4 | 9.1 / 13.8 | 28.6 / 29.1 | 27.8 / 28.6 | 13.05 / 13.37 |
| 3,000 | 78.8 / 80.0 | 38.2 / 50.8 | 80.0 / 50.8 | 30.1 / 35.8 | 14.28 / 14.54 |
| 10,000 | 309.0 / 376.8 | 156.5 / 225.8 | 376.8 / 225.8 | 30.1 / 32.5 | 14.50 / 14.80 |

Frame gaps include capture, so a rare long capture can be worse than p99 in a
small collection of long save windows. The headline maximum remains visible.
The mature 3,000-tick fixture stays below 100 ms, with median below 50 ms. The
10,000-tick fixture does **not** meet the 100 ms target: median about 156 ms and
maximum about 226 ms. This is not fully nonblocking or stutter-free. The initial
10,000-tick run measured 154 ms maximum; the later reset-fixture run found the
larger 226 ms outlier and takes precedence for the worst-case statement.

| Tick | Writer wall median s before / after | State assembly / JSON after median ms | SQL write / FULL commit after median ms | Main peak RSS MiB before / after | Child peak RSS MiB before / after | Save MiB before / after | Saved tick |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0.018 / 0.018 | 2.2 / 1.1 | 0.1 / 0.0 | 49.1 / 48.9 | 44.6 / 44.3 | 0.10 / 0.10 | 0 |
| 1,000 | 0.221 / 0.244 | 38.1 / 25.0 | 2.1 / 0.0 | 93.3 / 92.9 | 65.8 / 65.3 | 1.52 / 1.52 | 1000 |
| 3,000 | 0.859 / 0.872 | 139.2 / 83.0 | 6.4 / 0.0 | 215.2 / 214.5 | 158.0 / 153.1 | 5.25 / 5.25 | 3000 |
| 10,000 | 3.079 / 3.143 | 479.5 / 269.8 | 24.6 / 0.0 | 669.7 / 665.9 | 518.5 / 502.3 | 18.73 / 18.73 | 10000 |

RSS values are per-process high-water marks, including fixture reconstruction and
exact-state verification. They are not simultaneous aggregate RSS or a memory-leak
study. Main CPU and child CPU measurements are retained in JSON; main process CPU
includes setup/assertions, so it is not a pure gameplay-utilization percentage.
`simulation_ticks_per_second` includes all verification overhead; the table uses
`active_window_simulation_ticks_per_second` instead, measured only during saves.
All twelve final after checkpoints and live continuations compared exactly.

The main improvement is avoiding dataclass instance reducers during capture:
plain containers are encoded at one boundary and reconstructed in the spawned
child. Full canonical JSON assembly, two previous-world validations and FULL I/O
still cost seconds for large worlds; those costs remain off the gameplay thread.
Queue capacity remains one active write plus one boolean manual request.

Next engineering step if longer-history hitches are unacceptable: evaluate
explicitly immutable/versioned history segments or generation-aware snapshots,
with separate same-tick proof and profiling. Do not chunk mutable live objects
across ticks or weaken validation to hit a timing target. No such architecture
or G8 mechanic was implemented here.

```bash
.venv/bin/python -m research.saveguard_profile --modes spawn --out /tmp/saveguard-after.json
```

These are SDL-dummy operational measurements on the development host, not human
playtest approval. Legacy G1 retains its original synchronized worker; the
nonblocking terrain result must not be generalized to that compatibility launcher.

Capture timings were finalized before the subsequent hot-journal failure-path
corrections. No later change altered the capture implementation or moved work
onto the gameplay thread. The final writer adds a journal-existence check and,
only after a crashed transaction leaves a journal, explicit recovery in the child.
That rare recovery path is covered by tests, not included in routine timing tables.
Final operational smoke and regressions run against the delivered source.

## Actual changed-payload commit measurements

The reset-fixture paired run saves the same payload repeatedly: SQLite can avoid
physical page changes on those idempotent updates. Its rounded 0.0 ms commits are
**not** a claim that ordinary fsync is free. The initial advancing-world run also
measured genuinely changed payloads (repetitions 2 and 3), retained below. Its
slightly different snapshot ticks make these illustrative I/O costs, not exact
matched-performance deltas. Capture comparisons above use the controlled fixtures.

| Fixture | Actual snapshot ticks | SQL payload write ms | FULL commit ms |
|---:|---|---|---|
| 0 | 1, 1 | 0.24, 0.09 | 0.15, 0.01 |
| 1,000 | 1005, 1008 | 4.70, 4.94 | 0.82, 0.77 |
| 3,000 | 3015, 3030 | 20.67, 18.63 | 1.59, 1.54 |
| 10,000 | 10056, 10110 | 64.65, 68.33 | 3.45, 3.52 |
