# Operation God Complex — verified handoff

**G5, G6 and G7 completed.** Started from clean accepted G4
`0508849cea815f325e87973a06e810ad2e8c41ec` on a dedicated campaign branch.
No G8, modes, Ironman, predators, LLM behavior or civilization systems.

## Play

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_world
```

The new launcher creates/resumes **run-results/god-terrain/world.g5.sqlite**.
The original `python -m gnome_fortress.god_demo` and `.g1.sqlite` saves remain
separate and operational. A guaranteed fresh world uses an unused path:

```bash
.venv/bin/python -m gnome_fortress.god_world --new --db run-results/god-terrain/my-new-world.g5.sqlite
```

To resume that world, use the same `--db` without `--new`. Existing destinations
are never replaced by `--new` or legacy import. Never run two writers on a file.

**R/D** Rain/Drought, **E** Rupture, **F** Rewild, **P** Wellspring. Select then
click; terrain actions occur in ID order at the next complete simulation tick.
Bright preview cells are eligible now; earlier queued actions may change that.
Wellspring targets only one rock; other targets record an honest zero-change.
**T** inspects ordered tile history; **H** toggles small divine footprint marks.
**A → 5** asks the scripted Advisor about real land changes. **O** observes,
**F1/F2/F3** inspect gnome/powers/Life, **W** watches. Space, +/- , single-step,
S save and Escape save/exit retain their functions. No gnomes are directly commanded.

Rupture removes food and creates existing hazardous terrain, without instant
health damage. Rewild creates initially empty forest that regrows naturally.
Wellspring changes existing rock into existing freshwater mechanics. Neither
restoration nor a spring heals, resurrects, rewrites memory or erases past events.

## Delivered and executed

| Gate | Result | Feature commit |
|---|---|---|
| Versioned G5 storage, copy-only import | PASS; 28 focused tests | `5dae3be` |
| G5 Rupture and complete terrain ledger | PASS; 15 focused tests | `87627ec` |
| G6 Rewild and Wellspring | PASS; 21 focused tests | `7927e5c` |
| G7 history, footprints, UI and Advisor | PASS; 61 targeted tests and actual Pygame captures | `275c254` |
| Final integrity, regression and comparisons | PASS; **232 fast tests**, 22 UI/storage/operational checks | final verification commit containing this file |

Additional passes are not independent scientific samples. The initial broad
integration run passed 220 tests; adding operational/metadata checks produced a
230-test pass, followed by the final **232-test** pass after the last UI/terminal
fixtures. Initial failures and their fixes are preserved in [DEFECTS.md](DEFECTS.md),
not hidden by relaxed assertions. [Final fast log](verified-fast-tests.txt).
No long historical archive or 100,000-tick campaign was run.

The five conditions × three seeds × 3,000 ticks each passed exact independent
replay, tick-250 save/load and final save/load-plus-20 continuation. The untouched
worlds matched preserved Phase 3 World state exactly. Final populations:

| Seed | Untouched | Rupture | Rupture + Rewild | Spring | Combined |
|---|---:|---:|---:|---:|---:|
| 1 | 368 | 350 | 364 | 346 | 366 |
| 2 | 344 | 382 | 379 | 372 | 378 |
| 3 | 380 | 371 | 377 | 385 | 388 |

Effects are not uniformly helpful or harmful across seeds. These small finite
comparisons do not prove a general survival benefit. Rewild also transforms
natural hazards in its circle and converts former grass to forest, rather than
restoring original terrain. RNG paths diverge after changed choices. No individual
death is attributed to divine action merely because it occurred afterward.

A separate optional 10,000-tick combined check ended with 375 living of 2,063 total
individuals, preserving all 1,688 deaths. Replay and checkpoint continuation were
exact. This is not permanent-stability evidence. [Full study and caveats](EXPERIMENTS.md).

## Preservation and compatibility

- **538 existing files preserved**, including **418 research files**; only root
  README and shared God viewer have intentional edits among accepted G4 files.
- Eleven core/legacy modules, the mode contract, research storage and historical
  datasets remain unchanged. All five historical tag references match the G4 audit.
- Accepted G1/G2/G3/G4 writer snapshots import without source-byte changes and
  continue exactly for 90 ticks; original readers still read originals. The retained
  archived G1 fixture also imported and continued exactly.
- Default G4 viewer state, Watch/selection and rendered Life/Advisor pixel hashes
  matched the accepted implementation in an executed scripted comparison.
- New `.g5.sqlite` uses distinct SQLite identity, format and record version,
  transactional checksummed snapshots and strict validation. The old loader is
  intentionally unable to read it. No implicit or in-place upgrade.
- Explicit legacy import records source format, tick and legacy digest; it cannot
  overwrite an existing destination. [Instructions](../g5/FOUNDATION.md).

[Preservation/compatibility audit](verification/preservation.json). Full game/RNG
state is checkpointed; ephemeral Advisor, selection, scrolling and overlays are not.

## Captures, performance and limits

[Actual Pygame before/after/history/Advisor screenshots](../g7/REPORT.md) came from
natural seed-1 biology and real scripted keyboard/mouse inputs, not mockups or
forced biological events. The real display check ran 120 unpaused frames, retained
Watch and saved/reloaded exactly. Human usability sessions: none.

Dummy-display profiling measured about 4.5–4.6 ms/draw in mature/stress worlds.
The 1,005-intervention synthetic stress fixture updated an existing checkpoint in
about 0.97s; full snapshot loading/serialization remains the larger cost. No
unnecessary optimization was attempted. [Measurements and limits](PERFORMANCE.md).
History grows with actual events/requests; indexes avoid per-frame full rescans,
but this does not promise constant memory forever. No complete lifetime drinking
transcript, movement path, general causal explanation or Ironman recovery exists.

## Reproduction and commit history

[Prerecorded protocol](EXPERIMENT_PROTOCOL.md), [running journal](WORKLOG.md),
[architecture](ARCHITECTURE.md), [G5](../g5/REPORT.md), [G6](../g6/REPORT.md),
[G7](../g7/REPORT.md). Commands:

```bash
.venv/bin/python -m pytest -q tests research/test_analysis.py research/test_phase2.py research/test_study.py --ignore=tests/test_long_run.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m research.overnight_verify --output run-results/terrain-audit
.venv/bin/python -m research.overnight_study --output run-results/terrain-study/experiments --ticks 3000
SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy .venv/bin/python -m research.overnight_capture --output run-results/terrain-capture
```

Use an unused capture output directory; no preserved checkpoint should be reused
as a demo destination. Timings and frame-paced smoke tick counts vary with hardware;
fixed-input simulation state/digests do not. Get exact campaign commit hashes with:

```bash
git log --reverse --format='%H %s' 0508849cea815f325e87973a06e810ad2e8c41ec..HEAD
```

Final verification SHA and successful push/fast-forward status are supplied at
handoff. No further features are authorized or started by this delivery.
