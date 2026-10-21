# P0 — Project Saveguard

Saveguard preserves G7 and improves the existing stabilization attempts; it does
not implement G8. Starting checkout: clean main at `52bf735`. Accepted G7 and all
historical tags remain intact. Final delivered SHA is printed in the handoff;
`git log -1 --format=%H` identifies this checkout.

## Delivered

- Both gameplay launchers acquire canonical-path, lifetime flock ownership before
  loading/creating/importing; stopped processes retain ownership. Separate paths
  remain independent. Sidecars are retained, never manually deleted.
- Terrain autosaves capture one complete tick into detached bytes and keep stepping
  and rendering while a spawned process validates, serializes and writes. Flattened
  container capture reduces the measured pause without losing any retained history.
- A writer-drain gate prevents a parent crash from exposing its checkpoint to a
  replacement game while the orphan is committing. A not-yet-started orphan cannot
  write. No session FD is inherited by the spawned writer.
- One active save plus one boolean manual request; repeated S inputs coalesce.
  Failures preserve the previous checkpoint, visibly mark UNSAVED, pause and suppress
  auto-retry. Explicit S retries. Completion reports the snapshot's actual tick.
- Both writers reject decreasing ticks in the pinned transaction. Same-tick requests
  remain saveable. FULL sync, validation, checksums and format identities are retained.
- Active launchers explicitly recover valid SQLite hot journals while holding
  ownership. Public archive readers stay read-only. Surviving-owner retries recover hot journals
  in the delegated replacement child. Unsupported identities are refused
  before writable recovery, with no reseed or manual journal deletion.

## Measured result and limits

[Before](PROFILE_BEFORE.md), [after](PROFILE_AFTER.md), [design](DESIGN.md),
[diagnosis including defects](DIAGNOSIS.md).

The final paired comparison's 3,000-tick world (368 living) captured in 36–51 ms,
versus 67–80 ms before. The 10,000-tick world (373 living, 2,017 retained individuals,
107,609 objective events) captured in 155–226 ms, versus 291–377 ms before.
The earlier initial after measurement was 145–154 ms; the larger final outlier is
retained. **The 10,000-tick capture does not meet the 100 ms target.**

Multi-second validation/JSON/SQLite work stays off the terrain gameplay thread.
This is a bounded coherent capture, not a zero-stall or fully nonblocking claim.
The three-sample fixtures do not establish arbitrary-history latency bounds. Full
history still grows; queue size is bounded, historical state size is not. A future
immutable/versioned-history design needs a separate consistency proof and benchmark.
Legacy G1 retains its original synchronized worker, with ownership/recovery fixes;
its autosaves are not claimed to have the terrain performance improvements.

## Exact outcome evidence

[Matched experiment](evidence/replay.json): seed 1, three worlds (no saves,
synchronous checkpoints, detached checkpoints), fixed tick-based inputs for all
five powers, twelve snapshot boundaries through tick 2,400, final tick 2,401.
Every saved state and RNG matched its tick-specific reference while the live
world advanced. All final canonical digests match; reload at tick 20 includes
active Rain/Drought and queued Rewild and continues exactly. The run contains
429 non-founder births and 118 deaths. These are verification observations, not
claims of intervention benefit or individual counterfactual causality.

[Legacy compatibility](evidence/legacy-compatibility.json): generated actual G1
and G5 files using the preserved G7 source in a temporary directory. Current readers
match original digests and 60-tick continuation. The original baseline readers also
read current same-tick rewrites with identical digests. Source bytes are unchanged
by reading. No old player checkpoint or research archive was converted.

[Preservation audit](evidence/preservation.json): engine, model, biology/game rules,
Advisor, Life, presentation facts, terrain rules and game-mode contract match
accepted G7. All 425 baseline tracked research files and tag references are unchanged.
The previously added G7 autosave benchmark and new Saveguard harnesses are additions.
Ignored historical datasets were not rehashed; no archive campaign was repeated.

## Executed regression results

- [Focused final suite](evidence/targeted-tests.txt): **33 passed in 44.84 s**.
- [Fast final suite](evidence/fast-tests.txt): **235 passed in 139.02s (0:02:19)**.
- [Extra crash/retry probe](evidence/retry-recovery-tests.txt): **6 passed**, 13 deselected.
- [Forced hot-journal probe](evidence/hot-journal-tests.txt): **2 passed**, 16 deselected.

Earlier 232/234-test runs are retained as preliminary evidence, superseded by the
final fast suite. [Source hashes](evidence/tested-source-sha256.json) identify the
operational source/test content exercised. No full endurance or historical replay
campaign was run. The performance gate passes for the representative 3,000-tick
world; the longer-history 100 ms target remains unmet and explicitly reported.

## Process/failure coverage

| Case | Executed coverage |
|---|---|
| Same save / before load / canonical alias | Both CLI variants refuse before decoding deliberately invalid checkpoint |
| Different saves | Second independent path runs while first path is owned |
| SIGSTOP / SIGCONT / SIGKILL | Real harness owners, stopped refusal, resumed process, kill then exact relaunch |
| Normal exit | Existing real CLI shutdown test releases ownership and immediately reopens |
| Owner killed during active writer | Relaunch refuses until orphan finishes; then latest committed tick loads |
| Queued orphan / descriptor inheritance | Dead/wrong owner refuses before decoding; child has no owner-lock FD |
| Interrupted SQLite | Harness SIGKILL; plus forced cache spill creates a real hot journal in G1/G5 |
| Recovery safety | No ownership refused; foreign research identity refused before writable opening |
| Failed worker / retry / crash | Previous commit survives; broken pool is recreated; real hot-journal crash recovers on explicit retry while owner stays alive |
| Duplicate manual inputs | 100 S events coalesce into two snapshots, actual captured ticks reported |
| High-frequency autosaves | Current CLI interval-1/40-frame smoke reaches tick 38 exactly, one future enforced |
| Exit during pending save | Pygame Escape drains old snapshot, then latest tick commits under ownership |
| No mixed-tick snapshot | All five powers, queued/active/completed records, later live mutation, exact snapshots |
| Extinction | Detached checkpoint reload stays terminal with queued action; no resurrection/input |
| Research/legacy equivalence | Original readers, pinned reference tests, strict protected-path rejection |

## Operational Pygame evidence

[Trace](evidence/pygame-smoke.json), [actual screenshot](evidence/pygame-saving.png),
[actual CLI interval-1 shutdown](evidence/interval-one.json).
The scripted SDL-dummy Pygame loop used a controlled 0.5-second writer delay on a
fresh seed-1 world. While tick-0 saving was pending, the world advanced to tick 10,
Advisor, Life/Watch and land views accepted inputs, and a real Rupture request
completed. Navigation/casting consumed no simulation RNG. Escape occurred while
saving; the worker drained tick 0 and final flush committed tick 10 exactly.
Relaunch ownership was reacquired. This is an automated operational check, not a
human usability verdict or a claim the screen was physically displayed to a tester.

## Launch and safe owner recovery

First save/exit any already-running pre-guard version and wait for its terminal
prompt. Updates cannot retroactively lock a process running old code.

```bash
cd ~/gnome-fortress
git pull --ff-only
.venv/bin/python -m gnome_fortress.god_world
```

To inspect ownership (replace paths/PID only after identifying your actual run):

```bash
pgrep -af 'python.*gnome_fortress\.(god_world|god_demo)'
ps -o pid,ppid,stat,etime,args -p PID
cat run-results/god-terrain/world.g5.sqlite.lock
lsof run-results/god-terrain/world.g5.sqlite run-results/god-terrain/world.g5.sqlite.lock run-results/god-terrain/world.g5.sqlite.writer.lock
```

PID text is diagnostic; flock is authoritative. A `T` process is suspended and
still owns its world. In the terminal that suspended it, `jobs -l` then `fg %N`
resumes the identified job; use Esc and wait for final save/prompt. If that terminal
is unavailable, after verifying the PID and command, `kill -CONT PID` followed by
`kill -TERM PID` requests graceful shutdown and final saving. Do not issue those
commands against an unidentified/newer game. Never delete .lock, -journal, -wal or
-shm files. SIGKILL discards unsaved state and is not ordinary recovery.

After a save error, S explicitly retries; success clears UNSAVED but leaves the
world paused. Space resumes. Exit can block during its final save. No Ironman or
complete power-loss/corruption-repair guarantee is claimed. An unrecoverable or
unsupported checkpoint remains an explicit error, not a replacement world.

## Reproduce verification

```bash
.venv/bin/python -m pytest -q tests/test_saveguard.py tests/test_terrain_checkpoint.py tests/test_game_session.py tests/test_terrain_operations.py
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
.venv/bin/python -m research.saveguard_replay
.venv/bin/python -m research.saveguard_compatibility
.venv/bin/python -m research.saveguard_smoke --out /tmp/saveguard-smoke
```

The 20,000-tick endurance test and 72-archive campaign are deliberately excluded.
Profile commands are in the before/after documents. All destructive failure tests
use harness-owned children and temporary worlds; the player's live process/save
was inspected read-only and left running. Stop here; G8 remains unauthorized.
