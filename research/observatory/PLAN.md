# Founders' Observatory execution plan

1. Inspect Phase 3 agent fields, founding identities, scheduling and persistence.
2. Add an independent standard-library curses observer and pure text projection.
   Keep parentless founder records separate from scheduler slots. Read checkpoints
   through a read-only SQLite backup into temporary storage; never save the input.
3. Add focused tests for projection, navigation/resizing, controls, read-only loading,
   loading responsiveness and exact state equivalence. Run fast regression tests.
4. Capture the actual terminal, document launch/limitations and commit separately.

No engine, model, storage, scheduler or Pygame changes are planned. Loading is a
background operation; loaded inspection is frozen unless --live is explicit.
