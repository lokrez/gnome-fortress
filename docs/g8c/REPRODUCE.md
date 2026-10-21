# Reproducing G8C

Run from the repository using its existing `.venv`. Never use the owner's active checkpoint as an input to these scripts. The benchmark paths below are local fixture prerequisites, not portable bundled datasets. Their absence must be resolved by generating an independent fixture or copying a safely closed source under both ownership gates; do not silently substitute a smaller world.

- Young world: script constructs `TerrainWorld(1)`.
- Mature fixture: `/tmp/gnome-g8a2-generated-fixtures/26000.pickle`, trusted local generated seed-1 state.
- Giant fixture: `/tmp/gnome-deep-time/player-copy.g5.sqlite`, independent inode copy with protected-state payload SHA recorded in PREFLIGHT.md. Loading is expensive; allow more than 20 GiB free RAM for the owner/worker plus overhead and sufficient temporary disk. No hard links.

```bash
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
.venv/bin/python -m research.g8c.replay
.venv/bin/python -m research.g8c.profile --scale 0 --out /tmp/g8c-profile-new
.venv/bin/python -m research.g8c.profile --scale 26000 --out /tmp/g8c-profile-new
.venv/bin/python -m research.g8c.profile --scale player --out /tmp/g8c-profile-new
.venv/bin/python -m research.g8c.operation --scale 26000 --cold --out /tmp/g8c-operation-new
.venv/bin/python -m research.g8c.operation --scale player --out /tmp/g8c-operation-giant-new
```

Operation scripts create temporary independent save destinations, run the actual Pygame owner loop with SDL dummy, assert exact results, close ownership and remove only their own temporary checkpoints. The 26k run deliberately fails one child save and verifies explicit retry. Neither script is a human playtest. The giant private in-memory world progresses during the operational test; its source file does not.

`profile.py` records preparation units and GC, then removes per-block timers before 15 warm samples. Reference measurements used the accepted c88b217 implementation in an isolated reference checkout; raw measurements are in evidence/before. Do not overwrite checked-in evidence when repeating. `report.py` reads the committed paths to reproduce summary tables; percentile interpolation is documented in its source. `audit.py` is an environment-specific protected-source check that refuses an owned original instead of interfering with its process.

The normal player launch command is unchanged. Only pull verified work after the existing game exits cleanly; do not run a second process against the same save. User input, presentation and actual captured save ticks retain their existing meaning except the documented deferred unprepared request.
