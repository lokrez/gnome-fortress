# G5 — The First Scar

PASS. TerrainWorld now accepts deterministic one-shot `rupture` requests. Default
radius 2, integer circular row-major footprint, next complete-tick activation.
Grass/forest become existing hazard; stored food becomes zero. Rock, water and
existing hazards remain unchanged. Requests share stable IDs with Rain/Drought.
All due actions execute in ID order before normal regeneration, biology and
movement. A request completes at activation and never expires physically.

No RNG draws, direct health changes, relocation or scripted outcomes. A gnome
standing on newly hazardous ground receives no activation injury; inherited
movement applies hazard damage only when it subsequently enters hazard terrain.
This can include another hazardous neighbor. No earthquake casualty event exists.

Authoritative ordered transition records contain coordinates, old/new terrain,
old/new food, request/activation ticks, target/radius, changed count, food removed
and lifecycle. Zero-change and repeated requests remain visible with zero changes.
Validation rebuilds terrain composition from the format-epoch map and ordered
records; it rejects missing/duplicate/impossible transitions and inconsistent
summary/events. Historical food values are checked for bounds/local rules, not
claimed to be reconstructed through all past unrecorded eating/regeneration.
Python optimized `-O` operation is rejected to avoid disabling inherited integrity
assertions. Standard legacy execution is unchanged.

Executed Gate 2: **15 tests passed in 3.43s**, including foundation tests,
regeneration-boundary activation, occupied grass, no direct damage, edge footprints,
repeated overlap, no-op, RNG isolation, Rain accounting, replay, queued/completed
save continuation and malformed history rejection. See [log](rupture-tests.txt).
No historical replay campaign. Existing biology/scheduler inspected and inherited,
not reimplemented.

Runnable bounded demonstration:

```bash
.venv/bin/python -m research.g5_demo --output run-results/g5-demo
```

It requests at tick 9, activates at 10, and checks a loaded world matches through
110. [Actual output](demo.json). At this stage the new launcher still reuses legacy
Rain/Drought presentation; terrain controls are a separate G7 gate, not hidden
partial buttons. See [versioned persistence/import](FOUNDATION.md).
