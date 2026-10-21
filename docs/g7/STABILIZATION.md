# G7 stabilization — reported autosave pauses

Human report: entire world freezes, then resumes; header explicitly says SAVING.
Baseline: g7-verified / df3a3674fb19104f4be1a0a87c72aabd7474ad16.
This is a reported usability defect, not evidence of changed biological behavior.

Confirmed before changing code: the shared observer sets `saving=worker.pending`,
stops stepping and casting for the entire checkpoint, and targets 15 display FPS
while saving. G5 storage serializes the entire live World and validates/reconstructs
the previous database twice. The thread worker cannot allow live mutation during
that operation. Recorded mature-world updates cost about one second; costs grow
with history. The pause is intentional synchronization, but unsuitable for play.

Plan: leave legacy/research worker behavior intact. Terrain autosaves capture a
consistent detached logical state at a complete-tick boundary, then reconstruct,
validate and transactionally write it in a separate spawned process. The live
world may step and accept inputs once capture completes. Keep a visible SAVING
indicator, distinguish the saved tick from the current tick, coalesce requests,
retain failure suppression, and await writes before final live-state exit save.
No format changes or weakened integrity checks. Capture itself still has a finite
main-thread cost; do not promise zero latency indefinitely.

Verify snapshot isolation (including slots), live progress during pending writes,
exact stored state/RNG, continuation, failure/explicit retry, and clean shutdown.
Benchmark before/after on a generated mature fixture, never on the player's save.

## Implemented result

Only the terrain launcher uses TerrainCheckpointWorker. Legacy and research
workers retain their previous synchronization. A native in-memory snapshot is
captured on the owner thread at a complete-tick boundary, then sent to one
spawned writer process. Pickle is used only for trusted parent-generated IPC;
user checkpoints are still the original strict, checksummed SQLite/JSON format.
No user save/file is unpickled. The detached graph includes slots, agents, cells,
RNG, events and terrain records; mutable live objects are never shared.

After capture the live world steps and accepts interventions while SAVING appears
alongside RUNNING/PAUSED. These later actions are saved at a later checkpoint.
The interval is measured from the actual saved tick, not the current live tick.
Only one write may be pending. Explicit S requests during a write are coalesced
into a following snapshot, not silently discarded. Errors pause and suppress
repeated automatic retries; explicit retry can recover even after a writer process
crash. Ctrl+C is handled by the parent; the child finishes its transaction.
Exit/SIGTERM drains pending writes before the launcher's existing synchronous
save of the latest live world. No concurrent writers to the same database.

The old map/biology/history/RNG rules and save format are unchanged. An autosave
can finish with a saved tick older than the running world; this is normal and
explicit, not a claim that later actions are already durable. This remains a
prototype with manual saves, not Ironman or a command-recovery journal.

## Executed measurements

Generated seed 1, tick 3,000, 368 living; no player's checkpoint touched:

| Measure | Previous thread/live-state save | Detached-process save |
|---|---:|---:|
| Save wall time | 0.990 s | 1.076 s |
| Live simulation ticks during that save | 0 | 15 |
| Blocking capture/start time | n/a (whole write locks world) | 0.071 s |
| Maximum service gap in bounded loop | 0.109 s | 0.071 s |
| Saved state/RNG and live continuation exact | yes | yes |

The fix removes the whole-write simulation pause, not the finite snapshot-capture
cost. A short capture hitch can remain, particularly with much larger histories
or slower laptops. No promise of zero dropped frames or reduced total disk-write
work. This is a local generated-fixture timing, not a laptop measurement.

[Raw comparison](stabilization/comparison.json). Reproduce:

```bash
.venv/bin/python -m research.g7_checkpoint_benchmark
```

Tests cover detached slots/object history, movement and new actions while pending,
old-snapshot persistence, exact RNG continuation, errors, crashed process/retry,
and final save flush. A separate actual CLI SIGTERM check at checkpoint interval
1 advanced from tick 3 to 86 and exited with the exact latest reference state.
This was an SDL-dummy operational check, not a completed human playtest.

[Targeted tests](stabilization/targeted-tests.txt),
[fast regressions](stabilization/fast-tests.txt),
[shutdown evidence](stabilization/shutdown.json).
G8 remains unimplemented; the 20–30 minute human playtest remains pending.

Final executed regression result: **237 passed in 163.75s**. Targeted checkpoint,
terrain operational and legacy viewer checks: **16 passed in 6.03s**. The existing
research reference, terrain replay, legacy saves, corrupted/interrupted database,
Life/Watch, input locks for the original shared-world worker, and extinction tests
remain green. No research/engine/storage rule changes. G7's historical verified
tag is preserved; this correction is a separate stabilization commit.

## Follow-up: competing suspended launchers

During human playtesting, multiple Ctrl+Z-suspended terrain launchers were found
using the same save. Suspended processes retained SQLite read locks, preventing
the newer writer from committing. With explicit owner authorization to keep the
newest run, the older suspended copies were stopped. A consistent SQLite backup
was made first in the local run-results recovery directory; it is not committed.
The newest world subsequently committed at tick 20,917, and a host-level check
found no remaining open database handle. This confirms a successful checkpoint,
not completion of the full human usability playtest. No save/journal was deleted.

The terrain launcher now holds an Ubuntu advisory session lock before loading,
importing, creating, running or saving its world. A second updated launcher fails
clearly before touching the checkpoint, even if the first is suspended. The lock
is released by the OS on exit/kill; stale PID text does not prevent recovery.
The lock inode is retained to avoid races between launchers. Background snapshot
writers do not reacquire the launcher's lock. Different paths remain independent.
This does not retroactively protect already running old code, nor exclude external
SQLite tools or direct storage API callers. It is not Ironman enforcement.

New tests cover launch refusal without database modification, suspended ownership,
process-death recovery, clean shutdown and reopening. No simulation, save format,
research archive, or historical verification tag changes.

Executed follow-up verification: **14 passed in 4.55s** (session, terrain operation,
and isolated-checkpoint tests); **215 passed in 100.57s** with
`.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py`.
The 20,000-tick long-run test was deliberately excluded for this launcher-only
change. Raw results: [focused](stabilization/session-targeted-tests.txt),
[fast suite](stabilization/session-fast-tests.txt). These are the counts from this
invocation, not an inferred count from the earlier stabilization run.
