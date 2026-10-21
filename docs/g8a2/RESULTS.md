# G8A.2 — The Endless Chronicle

Baseline: `3baa31dcb3a7ee5e2d1db14b24259c92235df6dc`. The original game rules, art, camera and checkpoint format are preserved. This milestone changes how a complete snapshot reaches the worker, not which history is saved.

## Result

The representative generated 26,000-tick world (5,340 retained gnomes / 290,808 events) now captures warmed snapshots in approximately **17 ms** in the direct probe. In the final actual X11 game operation, all four capture/start calls, including a failed write and its explicit retry, took **17.7–20.8 ms**. The previous complete-graph capture was approximately **475 ms median** in the new baseline probes, consistent with G8A.1's half-second finding.

Prepared event/terminal-record bytes are reused; mutable living gnomes, terrain, intervention ledgers, scheduler and RNG are detached at tick T. The pool feeder copies immutable history bytes asynchronously. The worker assembles a complete World and uses the unchanged validated G5 writer. History is never dropped, summarized or replaced by an external delta file.

Cold manual saves remain slower: an immediate 26k capture without preparation measured **501 ms**. Cold preparation is budgeted, not hard real-time: the direct multi-size probe includes a **108 ms** allocation/GC outlier. Warm ordinary autosave interruption meets the requested <50 ms typical / <100 ms worst targets in these bounded tests. We do **not** claim all startup or preparation frames are under 100 ms, or that every history size has been verified.

## Verification actually executed

- **282 fast-suite tests passed in 161.96 s**, with the established long research run excluded. Existing Saveguard assertions and old tests are unchanged. [Log](evidence/fast-tests.txt)
- **14 targeted snapshot tests passed in 18.08 s** after final changes, including new mutation, value-equality, source-replacement, cache corruption/retry and tick-detachment checks. [Log](evidence/snapshot-final.txt)
- Two matched seeds, each through tick 2401, compared no saves, accepted full capture and optimized saving. Twelve snapshots per condition include queued/active Rain/Drought, Rupture/Rewild/Wellspring, natural births/deaths, sleep, memory and regenerated resources. Complete state/RNG and stored JSON payload/checksum agree. Tick-20 reload and subsequent tick-based inputs reproduce the final state. [Exact hashes](evidence/replay.json)
- The full-reference capture helper produces byte-identical IPC to the accepted capture function on two seeds at ticks 0 and 500. [Evidence](evidence/accepted-capture.json)
- Existing subprocess Saveguard tests executed second-instance rejection, SIGSTOP ownership, owner kill, writer gate/orphans, interrupted SQL transactions, hot journals, pending shutdown, request bursts, failed save/retry, worker crash, extinction and legacy G1/G5 handling. No destructive tests used the owner's process.
- A generated 26k mature-world desktop run performed three completed background checkpoints (two automatic, one explicit retry), one deliberately failed automatic write, S retry/resume, real Advisor/navigation/power input, final save and reload continuation. [All frame/preparation/save timings](evidence/operation.json), [summary](evidence/operation-summary.json), [actual SAVING capture](evidence/mature-saving-active.png).
- Matched 600-tick mature-world throughput: 2.277 s without preparation, 2.378 s with four prepare calls per tick: **4.42% additional elapsed time**, exact final state. An earlier ~20% cost was diagnosed and removed; those measurements remain in evidence.

## What the desktop trace says

The world was not frozen for the approximately nine seconds of strict validation/writing per checkpoint. It continued simulating and drawing; completion reports retained the captured tick. A living individual was explicitly selected for follow during saving, and normal death/follow handling remains unchanged. World Happenings reflected real appended records. The only injected physical action was a genuine Rain request through the existing UI; no biological events were manufactured.

The maximum overall frame gap was **135.92 ms**, a one-time cold startup/index transition with no save pending. Warm frame maximum was **83.58 ms**; overall p99 was **26.27 ms**. The raw trace and summary retain it rather than excluding it from the evidence. Warm and all-frame maxima are separately reported by actual preparation readiness. Human smoothness approval remains pending.

Final exit saved the current world and released/drained its worker; the saved tick is recorded separately from the later +30-tick reload check. The actual launcher still performs its existing final synchronous save. Wait for the terminal prompt; do not suspend the game with Ctrl+Z or start another copy while it is exiting.

## Memory and remaining costs

A fresh-process 26k resident probe increased from about 354 MiB before preparation to about 380 MiB after preparation, and about 385 MiB after twenty captures. This is observed RSS, not exact allocation attribution. Immutable cache bytes total about 24 MiB, plus tracking metadata. Block counts do not multiply with save generations. Large canonical history and its cache still grow linearly; this is not an infinite-memory solution.

The strict writer still takes around nine seconds and peaks around 1.2 GiB during full old-state validation/JSON assembly. At accelerated speeds it can limit how often a durable checkpoint completes; the original single-future/coalesced-request policy remains. Cold preparation and immediate cold saves can still hitch. Normal low-level developer edits bypassing instrumentation require explicit cache invalidation; see the mutability audit. No Ironman or tamper-resistance claim is made.

50k/100k extensions were not launched. The measured 26k verification and writer memory/latency were sufficient for the specified representative-world target; larger horizons need a separately budgeted stress pass. No research endurance/archive campaign was rerun.

## Preservation

[Source/tag audit](evidence/preservation.json): engine/model, terrain/power rules, RNG/scheduler, art, camera, research and game-mode contract are unchanged. G5 application ID/schema/format/checksums/FULL synchronization/readers/writers, legacy import, lifetime ownership and crash recovery sources are unchanged. Only the terrain IPC worker, its new disposable cache module and an optional prepare hook in the existing loop change runtime behavior.

The owner's existing world was never loaded or written by this work. Its running owner/writer were inspected read-only and left intact. No lifetime lock descriptor was visible on that old running owner; new protections cannot be retrofitted into an already-imported executable. Exit the old game normally before relaunching. New lock behavior was tested only on isolated paths.

## Run and reproduce

The launch command is unchanged:

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_world
```

Generated-fixture commands (never use the player's save):

```bash
.venv/bin/python -m research.g8a2_profile --fixtures /tmp/gnome-g8a2-generated-fixtures
.venv/bin/python -m research.g8a2_after
.venv/bin/python -m research.g8a2_worker_profile
.venv/bin/python -m research.g8a2_throughput
.venv/bin/python -m research.g8a2_verify
SDL_VIDEODRIVER=x11 .venv/bin/python -m research.g8a2_operation
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
```

The baseline profiler explicitly constructs the accepted full graph from a fresh unprepared World and can run at this commit; generated fixture IPC is trusted local test data, not an import format for arbitrary files. Profiling defaults write this milestone's evidence paths: choose `--out` where supported or preserve the committed results before reproducing. The cache is never required to load a G5 checkpoint. No G8B or new gameplay was started.
