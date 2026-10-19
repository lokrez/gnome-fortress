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
.venv/bin/python -m pytest -q -s
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

The verified Phase 0 baseline is tagged `phase0-verified` (`f32c1a6`). The original
simulation source and tests remain unchanged. See the [population study report](research/phase1/REPORT.md)
for ten 20,000-tick runs, CSV data, plots, observer verification and controlled-memory
experiment designs. Reproduction instructions are in the
[data dictionary](research/phase1/DATA_DICTIONARY.md).

## Phase 2 memory, scaling and extended survival

See the [Phase 2 experiment report](research/phase2/REPORT.md) for matched memory
ablations, five scheduler capacities and three 100,000-tick endurance worlds.
The standard rules and 60-slot default remain unchanged.
[Reproducibility and data](research/phase2/DATA_DICTIONARY.md).
