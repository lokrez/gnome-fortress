# Performance and operational limits

Profiled before considering optimization. No blocking rendering/index regression
was demonstrated, so no engine/storage optimization or unrelated refactor was
attempted. Single measurements under concurrent campaign/regression load; these
are engineering observations, not hardware-capacity certification.

| Fixture | Living / retained | Events | Requests | Frame ms* | New save s | Update save s | File MiB |
|---|---:|---:|---:|---:|---:|---:|---:|
| young | 60 / 60 | 60 | 0 | 3.32 | 0.005 | 0.033 | 0.10 |
| mature-combined | 366 / 610 | 27,249 | 5 | 4.50 | 0.239 | 0.983 | 5.27 |
| synthetic-1000-noops | 366 / 610 | 29,259 | 1005 | 4.64 | 0.319 | 0.975 | 5.94 |

*30 read-only draws under SDL dummy, not real-display FPS or a human session.
The synthetic 1,000 no-op requests target existing water and deliberately stress
history/storage without creating fake biological outcomes. It is not natural play.

All steady refresh checks processed zero historical records again. Initial indexes
for the mature/stress worlds took roughly 5–7 ms. Corner overlays are bounded by
map area; transition-reference storage still grows with accepted history. No
constant-memory claim is made. The new terrain history adds no per-frame log scan.

Profiling the stress save identifies reconstruction/deepcopy of old checkpoints
and dataclass/JSON serialization as the dominant costs. Existing-file saves check
old data before and within the write transaction, preserving fail-closed behavior.
New-file timings alone would understate normal update cost; both are reported.
The draw profile is dominated by existing map/agent drawing and font work, not
provenance queries. No optimization was necessary for this bounded milestone.

Peak RSS for the profiling process: **214.2 MiB**, including young, mature and stress
worlds plus save/load verification. It is not the memory cost of one production
world. See per-worker CPU/RSS in the matched study and the separately labeled
10,000-tick run. Snapshot growth remains a limit of prolonged play.

Operational tests use a real pending checkpoint callback and confirm every power
cast and simulation step is blocked while inspection/Advisor remain serviced.
Failed periodic saves pause and suppress automatic retries; explicit S retry can
restore checkpointing. A real child process terminated mid-SQLite transaction
left the prior committed state loadable. SIGTERM and explicit exit save remain
functional. An extinct G5 save with an unapplied queued action stays terminal
after reload; it cannot activate that action, step or cast to resurrect the run.

These are transactional prototype guarantees, not Ironman, durable command
journaling, recovery from arbitrary disk damage, or protection against an owner
modifying files. One writer per save remains required. Unsaved ticks/requests
can be lost on a crash. No manual rollback enforcement or mode selection added.

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m research.overnight_profile --output run-results/terrain-profile
```

[Raw measurements](performance/profile.json) · [Save profile](performance/save-profile.txt)
· [Draw profile](performance/draw-profile.txt) · [Operational checks](ui-integrity-tests.txt).
