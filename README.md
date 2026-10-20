# Gnome Fortress

A local, deterministic artificial-life prototype for Ubuntu. A seeded 48 × 32 world
starts with exactly **60 distinct founding gnomes**. The simulation runs independently
of its Pygame observer and checkpoints to SQLite. No network services, LLMs or game
framework are used.

This is an experiment in observable agent behavior. Its needs, reproduction rules,
interaction rewards and learning update are explicitly programmed. It does not model
civilizations or claim that complex social organization has emerged.

## Run

Python 3.11 or newer is required. This checkout already has an isolated `.venv` with
its tested dependencies installed. From this directory:

```bash
cd ~/gnome-fortress
.venv/bin/python -m gnome_fortress
```

For a fresh checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-tested.txt
.venv/bin/python -m gnome_fortress
```

On Ubuntu, install `python3-venv` if creating the environment reports it missing.
The viewer uses `pygame-ce` (the Pygame community edition, imported as `pygame`).
The headless engine and SQLite persistence use only the Python standard library:

```bash
python3 -m gnome_fortress --headless --seed 2026 --ticks 5000 --db experiment.sqlite
```

An existing database resumes automatically; `--ticks` adds ticks to the loaded world.
`--seed` applies only to a new world. To explicitly replace a checkpoint:

```bash
.venv/bin/python -m gnome_fortress --new --seed 42 --db alternate.sqlite
```

The default checkpoint is `fortress.sqlite` in the working directory. Keep one process
per database. Checkpoints occur every 300 ticks and on normal exit, Ctrl+C, or SIGTERM.
`--checkpoint-every N` changes that interval. Forced termination can lose ticks since
the last committed checkpoint. Saving is transactional. Back up the SQLite file when
the simulation is stopped. Console output reports population, event counts and a full
state SHA-256 digest.

## Observer

- **Space**: pause/resume.
- **+ / −** or **Up / Down**: speed, from 1 to 300 ticks per second.
- **.**: advance one tick while paused.
- **Click** a gnome: inspect it; repeated clicks cycle through overlapping identities.
- **Tab**: inspect the next identity, including deceased gnomes.
- **S**: checkpoint; **Esc** or close window: checkpoint and exit.

Green bars show actual food quantities, blue cells are water, gray cells are
impassable rock, and red cells damage agents that enter. Gold dots are awake gnomes,
blue dots are sleepers, and crosses mark deaths. Shared cells are allowed, so dots
can overlap. The inspection panel shows the selected agent's actual needs, action,
traits, movement associations, directional relationships and recent memories.

Pause, speed, selection and window events do not change world state. A requested
speed is a pacing target, not a guarantee; overload slows rendering and simulation
without skipping world ticks. No world-editing interventions exist in this milestone.

## Verify

```bash
.venv/bin/python -m pytest tests research -q -s
```

The full suite includes a 20,000-tick accelerated run plus 100 continuation ticks.
The observer tests run automatically using SDL's dummy display, without requiring
a desktop. To exercise the bounded observer command directly:

```bash
SDL_VIDEODRIVER=dummy .venv/bin/python -m gnome_fortress --frames 5 --db smoke.sqlite
```

See [VERIFICATION.md](VERIFICATION.md) for measured results and
[ARCHITECTURE.md](ARCHITECTURE.md) for ordering, scientific constraints, limitations,
and the next research experiment. [PLAN.md](PLAN.md) records the implementation steps.

## Phase 1 population study

The verified Phase 0 baseline is tagged `phase0-verified` (`f32c1a6`). The preserved Phase 0
source and tests remain available at that tag. See the [population study report](research/phase1/REPORT.md)
for ten 20,000-tick runs, CSV data, plots, observer verification and controlled-memory
experiment designs. Reproduction instructions are in the
[data dictionary](research/phase1/DATA_DICTIONARY.md).

## Phase 2 memory, scaling and extended survival

See the [Phase 2 experiment report](research/phase2/REPORT.md) for matched memory
ablations, five scheduler capacities and three 100,000-tick endurance worlds.
The standard rules and 60-slot default remain unchanged.
[Reproducibility and data](research/phase2/DATA_DICTIONARY.md).

## Phase 3 background operation

The default remains 60 decision slots. Existing standard 60-slot Phase 0–2
checkpoints resume automatically. Experimental capacity or ablation archives still
require their matching research configuration. The observer stays responsive while checkpointing, with simulation
held at a complete tick until the writer finishes. Paused observation sleeps and
avoids repeated redraws.

```bash
.venv/bin/python -m gnome_fortress --db fortress.sqlite --rate 15 --checkpoint-every 300
.venv/bin/python -m gnome_fortress --paused --db fortress.sqlite
.venv/bin/python -m gnome_fortress --headless --forever --rate 60 --stats-every 10 --db background.sqlite
```

Ctrl+C or SIGTERM commits and stops; restarting the same command resumes. Omit
`--rate` for unpaced finite/headless science. `--stats-every 0` disables periodic
stderr statistics; stdout retains the final population and original state digest.
Keep one process per database. Do not run an older writer against the new integrity
format; original archived files remain loadable. Corrupt/incomplete checkpoints
are rejected rather than silently reseeded. Backups are still needed for storage
device failure or corruption after a successful commit.

See the [Phase 3 engineering report](research/phase3/REPORT.md) for measurements,
exact equivalence coverage, persistence recovery tests, limitations and reproduction.

## Founders' Observatory (terminal)

From any terminal on Ubuntu:

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.observatory
```

This creates the standard seeded world, paused, without writing files. All 60
original founders remain selectable, including after death. Arrows/Tab select;
PgUp/PgDn scroll the inspector; Space pauses/resumes; `.` advances one paused tick;
`+`/`-` change simulated ticks per second; `[`/`]` change display refresh; `q` quits.
Use `--seed 42` to choose initial conditions. At 140 columns by 35 rows the entire
roster and the first inspector section fit together. An 80x24 terminal also shows
the whole roster with a shorter inspector; smaller terminals scroll.

To inspect a checkpoint, append `--checkpoint PATH`. Inspection is frozen and
never saves. Add `--live` to allow unsaved continuation of a loaded copy, initially
paused. **All progress in this observer is discarded on exit.** Use the standard
Pygame/headless application for persistent runs. Checkpoints must be closed,
rollback-mode SQLite files without WAL/journal sidecars; the observatory refuses
files needing recovery. Loading/indexing runs in a worker so the terminal can
redraw and process quit; exit waits for an in-progress worker to finish.

The terminal observer uses Python's standard Ubuntu curses support, with no new
package dependencies. [Observatory verification and limitations](research/observatory/REPORT.md).

## Phase 4A: opt-in first-conversation experiment

The standard simulator remains unchanged. A separate experiment adds a single
experience-grounded hazard association to existing local social interactions.
Run the fast two-gnome demonstration and its controls:

```bash
.venv/bin/python -m research.phase4a_demo
```

Start a new experimental world in the observatory:

```bash
.venv/bin/python -m gnome_fortress.observatory --communication social --seed 1
```

The condition can be `individual` (communication off), `social` (attenuated
association transfer), or `sham` (masked-message interaction control). No flag
means the unchanged standard World. Space resumes; `l` switches to living
descendants and `f` returns to the 60 founders. PgUp/PgDn scroll provenance,
received `hear` episodes and actual communication events. Experimental worlds are
still unsaved in the observatory.

To inspect the completed pilot, initially frozen and read-only:

```bash
.venv/bin/python -m gnome_fortress.observatory --communication social --checkpoint research/phase4a/results/pilot-01-social.sqlite
```

Pilot SQLite files are local generated artifacts, excluded from Git. Reproduction
commands, published CSV/results, limits, persistence format and evidence are in
[the Phase 4A report](research/phase4a/REPORT.md). Received information changed
movement before firsthand hazard exposure in controlled probes. **A survival
benefit or emergent culture has not been established.** No endurance campaign
was run for this milestone.

## Phase 4B: the telephone experiment

Run the controlled three-gnome demonstration (no files written by default):

```bash
.venv/bin/python -m research.phase4b_demo --seed 1
```

A physically encounters a hazard; prescribed local meetings allow A to inform B,
then B to inform C. C's scored movement uses the original engine. Individual,
direct-only, multihop, masked and irrelevant-content controls are printed together.
This is an experimental harness, not naturally emerging dialogue.

Save a new multihop checkpoint and inspect C read-only:

```bash
.venv/bin/python -m research.phase4b_demo --checkpoint run-results/telephone.sqlite
.venv/bin/python -m research.phase4b_inspect run-results/telephone.sqlite --agent 3
```

Create `run-results` first if it does not exist. The demo refuses an existing
output path. The companion inspector shows A/B/C source IDs, physical grounding,
receipt locations/ticks, firsthand status at acquisition, association inputs and
C's recorded movement. It also works with the locally generated experiment file
`research/phase4b/results/demo-multihop.sqlite`. The existing Observatory and all
Phase 3/4A application files remain unchanged.

[Phase 4B findings, control table, bounds and reproduction](research/phase4b/REPORT.md).
The engineered chain changed hazard entry to safe movement in 20 of 64 matched
seeds. The warning only breaks a one-point scoring tie in this fixture; neither
natural multihop prevalence nor population survival benefit has been established.

## Terrain gameplay prototype — G5–G7: God Complex

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_world
```

This separate launcher creates/resumes `run-results/god-terrain/world.g5.sqlite`.
Your legacy `.g1.sqlite` game stays separate. For a fresh run, use `--new --db`
with an unused `.g5.sqlite` path; `--new` never replaces an existing world.

**E** Rupture permanently fractures grass/forest; **F** Rewild turns hazard into
forest; **P** Wellspring turns one rock into water. **R/D** retain Rain/Drought.
**T** inspects a tile's real ordered history, **H** toggles divine footprints,
and **A → 5** asks the Advisor about actual terrain changes. Gnomes react through
existing independent needs, movement and learning. Restoration never resurrects
individuals or erases earlier events. **O**, **W**, **F1–F3**, pause, speed, save
and exit remain available.

See the [overnight handoff](docs/overnight/HANDOFF.md), [G5 persistence/import](docs/g5/FOUNDATION.md),
[G5 Rupture](docs/g5/REPORT.md), [G6 restoration/springs](docs/g6/REPORT.md),
and [G7 controls/history/screenshots](docs/g7/REPORT.md). This is a terrain prototype,
not release-mode selection or Ironman crash recovery.

## Playable God prototype — G4: The Advisor

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_demo
```

Choose **Rain (R)** or **Drought (D)** and click the map. **O** returns to observation,
**Space** pauses, **+/-** changes speed, **S** saves, and **Esc** saves and exits.
The separate gameplay save resumes on the next launch. This is not Ironman.

[G3 Life/Watch controls, actual screenshots and verification](docs/g3/README.md).

Press **A** or click **Advisor** for four scripted dialogue topics, factual world
and gnome summaries, intervention accounting and navigation. Use number keys or
mouse; **0** backs/closes. Escape still saves and exits. See the
[G4 Advisor guide and verification](docs/g4/README.md).
Use F3 for Life, W to watch, and Direct family to navigate parents and children.
The Life timeline presents recorded events, without fictional narration.
[G2 presentation report](docs/g2/README.md) remains preserved.
Use F1/F2 for individual/intervention details and Page Up/Page Down or the mouse
wheel to browse real recorded events. Existing G1 saves resume without conversion.

[Future Game Mode Design Contract](docs/game-modes/CONTRACT.md) is documentation
only; Ironman and release-mode selection are not implemented.
[G1 baseline report and resource rules](docs/g1/README.md) remain preserved.
The default research simulation remains available through its original launcher.
