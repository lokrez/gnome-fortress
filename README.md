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
