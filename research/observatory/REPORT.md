# Founders' Observatory

Baseline: `phase3-verified`, `2f5213c23300e61330ea665bfb4789622bf38bc6`.
This observational milestone adds one independent terminal module. Every existing
Python package file is byte-for-byte identical to that baseline; no biological,
learning, scheduler, Pygame, or persistence implementation changed. Existing tags,
research data and historical results are preserved.

## Launch and controls

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.observatory
```

Starts seed 1, paused, with the original 60 founders and 60 scheduler slots.
Optional arguments: `--seed 42`, `--rate 10`, `--refresh 5`.
Append `--checkpoint PATH` for frozen, read-only inspection; append `--live` to
permit unsaved continuation of that loaded copy. Both modes start paused.

Arrows or Tab select a founder. PgUp/PgDn scroll inspector fields. Space resumes
or pauses; `.` performs exactly one tick while paused. `+`/`-` set simulation
pacing (0.25–1,000 ticks/s); `[`/`]` set display refresh (1–30 Hz). `q`, Esc or
Ctrl+C exit. There is no save control, autosave, or shutdown write. Progress is
intentionally discarded; the existing Pygame/headless application remains the
persistent runner. In frozen inspection, simulation controls do not mutate state.

At 140x35, the six-column roster and inspector appear side by side. At 80x24,
all 60 fit above a shorter inspector. Smaller terminals scroll the roster to
keep selection visible and independently scroll inspector text. Roughly 30x12
is a practical minimum; extremely small terminals necessarily truncate labels.
Status codes are A (alive/awake), S (sleeping), D (deceased); `>` marks selection.
Resizing recomputes layout. Identity comes from sorted parentless agent records,
not current scheduler assignments, so descendants never replace founders.

## What makes the founders different

Founders have persistent IDs 1–60 and seeded names `Gnome 00001` through
`Gnome 00060`, no parents, birth tick zero and initial ages sampled from
120–300. They have no authored psychological biographies. The six inherited
traits are integer values in 0–100; founders are sampled from 20–80:

| Trait | Existing programmed role |
| --- | --- |
| curiosity | Bonus for moving to an unvisited location |
| caution | Hazard terrain penalty |
| sociability | Social interaction propensity/reward and proximity scoring |
| fertility | Reproduction probability with an eligible nearby partner |
| stamina | Age limit, `1800 + 12 * stamina` |
| vision | Manhattan sensory radius, `3 + vision // 25` |

Seed 1 happens to generate 60 distinct trait vectors; this is measured, not a
new uniqueness rule. See `integrity-check.json` for observed ranges.

The inspector shows ancestry, child count, biological age/health/needs, location,
sleep deadline, cooldown, latest action, inherited traits, eligible/assigned
scheduler state, learned values, retained episodes, outgoing relationship values,
visited-location count, and the latest 12 significant events matching the
founder's actor/target ID. All available episodes and outgoing relationships
can be reached by scrolling; they are not silently cut to a first page.

Inherited tendencies are labeled separately from learned associations. Only
`move:*` association values enter movement scoring. Relationship values are
directional, not evidence of mutual friendship. Assigned slots are retained
snapshots, not proof of decisions executed. Dead founders show their legitimate
terminal state, not fabricated ongoing experience.

## Checkpoint safety and responsiveness

A worker reads a closed rollback-mode SQLite checkpoint with `mode=ro`, backs it
up into temporary storage, loads/validates that copy through the existing loader,
and indexes events before handing the world to the UI. Temporary files are
removed. The recovery-capable loader never receives the original archive path.
WAL databases and WAL/journal sidecars are refused; use a clean, closed exported
checkpoint. Do not inspect a database while another process is writing it.

Navigation is serviced while loading; no simulation exists in the UI until the
worker hands it over. Quit requests are accepted while loading, but process exit
waits for the worker to finish. The UI does not implement loading cancellation,
checkpoint writing, or progress percentages. Loading retains the existing full
world/history memory cost. Live stepping is time-budgeted between input polls;
a single unusually expensive engine tick can still delay input. This is not a
separate simulation worker or a real-time execution guarantee.

Refresh and pacing are separate wall-clock controls. The engine receives only
whole sequential ticks and no UI clocks/randomness. Rendering never calls
`state()`/`digest()` or scans complete history repeatedly. Only new event tails
are indexed; each founder keeps references to the latest 12 matching events.
Paused loops sleep 50 ms and redraw only when content changes.

## Observations and terminal verification

The actual Phase 2 seed-1 100,000-tick archive loaded successfully:
60 founders, all deceased; living population 373; 20,792 descendant births and
20,479 deaths. Accounting: `60 + 20792 - 20479 = 373`.
The source SHA-256 was unchanged after snapshot inspection and terminal capture.
Measured snapshot load: 6.40 s; founder-event indexing: 0.33 s; average 140x35
layout projection: 1.52 ms over 50 calls. These are a single sample, not a
controlled benchmark. Raw measurements are in `archive-check.json`.

Real PTYs exercised startup, Tab selection, single-step, inspector scrolling,
resize from 140x35 to 60x18, and clean quit. Both new-world and mature-checkpoint
captures completed without tracebacks. This was automated terminal verification,
not a human visual review of every screen. Reproduce with:

```bash
.venv/bin/python research/observatory/capture.py
.venv/bin/python research/observatory/capture.py research/phase2/data/endurance/seed-01/final.sqlite
```

`fresh-terminal.ansi` and `checkpoint-terminal.ansi` contain actual terminal bytes;
`fresh-screen.txt` and `checkpoint-screen.txt` are readable exports of the same
presentation projection. Capture JSON files record completion and process CPU
seconds, including startup/loading; they are not paused-CPU benchmarks.

A first real-PTY archive attempt exposed a UI-only defect: `curses.napms` held
the interpreter lock while idle, starving the loading worker. It was replaced
with `time.sleep`, which releases the lock. Successful archive capture and a new
real-PTY checkpoint regression test verify the correction. An earlier test-only
fixture also attempted to save over its deliberately corrupted database; the
fixture now removes that file first. No simulation defect was found or fixed.

## Verification and limits

The focused suite was run first. Tests cover stable founder IDs, permanent
founder selection after death/birth, actual fields, missing optional information,
alive/sleeping/dead status, directional history, 80x24/all-60 layout, small
terminals, pause/single-step, frozen inspection, legacy/current checkpoint loads,
source bytes unchanged, corrupt/missing/journal rejection, loading controls,
paused redraw/sleep, and live equivalence at different display refresh rates.

Exact full-state comparisons include RNG, all agents and events. Existing
Phase 2 reference-world equivalence tests remain unchanged and are included in
the fast regression run. Test commands/results are recorded in `TEST_RESULTS.md`.
**62 fast regression tests and 25 research tests passed (87 total).**
The prolonged unattended test and full historical archive campaign were not rerun;
this milestone does not change their simulation implementation.

Complete decision histories are unavailable in the model. Only the latest 64
episodes survive per agent; bounded memory is an existing rule. Optional missing
presentation fields are labeled unavailable rather than filled with invented
attributes. Older model records must still be supported by the existing loader;
the TUI does not repair damaged archives or introduce schema migrations.

No social learning or new behavior is inferred from this interface. The next
research question remains whether useful information can be transmitted between
individuals and survive across generations; that requires a separately designed
experiment and is outside this milestone.
