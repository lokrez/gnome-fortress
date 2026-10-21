# Reproduce Deep Time

Use the campaign revision and its original Python/Pygame environment. Research
plotting additionally needs NumPy and Matplotlib (already installed here).
No networking or model API is used. Commands below run from the repository root.

Generate seed-1 fixture worlds at 1,000/3,000/10,000/26,000 ticks without touching
any gameplay checkpoint. Save trusted local pickles under
`/tmp/gnome-g8a2-generated-fixtures/{tick}.pickle`. Only read pickles you generated
locally; pickle is executable data. Generation uses `w=TerrainWorld(1); w.step(tick-w.tick)` at each listed
checkpoint and `pickle.dumps(w, protocol=5)`. Do not copy or open a live player database without its ownership gates.

Storage profiles:

```
.venv/bin/python -m research.deep_time.profile_storage --scale 26000 --reference --out /tmp/before.json
.venv/bin/python -m research.deep_time.profile_storage --scale 26000 --out /tmp/after.json
.venv/bin/python -m research.deep_time.profile_snapshots --scale 26000 --out /tmp/snapshot.json
.venv/bin/python -m research.deep_time.operation --reference --out /tmp/view-before.json
.venv/bin/python -m research.deep_time.operation --out /tmp/view-after.json
```

`--reference` executes pinned accepted storage from Git, not an edited facsimile.
The player-scale profile and shutdown scripts **only** use the independent
`/tmp/gnome-deep-time/player-copy.g5.sqlite` prepared under ownership gates. They
must never be pointed at the protected original. Keep sufficient disk space and
run large profiles sequentially. No profiler advances that private real world.
Generated-world operation uses its own temporary save path and does advance it.
SDL dummy runs the real Pygame renderer but is not a human playtest.

Scientific studies (declared protocols are adjacent):

```
.venv/bin/python -m research.deep_time.inheritance
.venv/bin/python -m research.deep_time.ecology --pilot
# Inspect the pilot estimate before launching:
.venv/bin/python -m research.deep_time.ecology
.venv/bin/python -m research.deep_time.analyze
```

Fixed seeds and PCG64 streams are documented in the source and JSON. The toy
inheritance RNG intentionally differs from production Python Random. Matched toy
conditions share proposal uniforms and mutation/rounding streams. After changed
selection/arithmetic creates different populations, matching random inputs does
not mean matching parents or trajectories. Full ecology keeps Python Random and
all production rules. Exact reference replay is checked independently.

Regression:

```
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
```

Do not rerun old endurance/archive campaigns for this change. Do not overwrite
historical evidence directories. Use `--out` for fresh benchmark outputs.
