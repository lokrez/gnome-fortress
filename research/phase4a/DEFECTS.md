# Phase 4A defects and experimental gaps

2026-10-20, before correction: the new experimental `state()` returned its
provenance dictionary by reference. A checkpoint rollback test retained a state
snapshot, stepped the world, and found the retained snapshot had changed. SQLite
rollback itself preserved the saved state correctly. Fix the new state projection
to copy nested provenance records, and test both snapshot and restored ownership.
This does not affect the Phase 3 engine or the communication decision mechanism;
JSON checkpoints/digests serialize immediately, so existing pilot output remains
valid. Do not interpret the failed snapshot test as verified persistence until
it passes after correction.

The ownership regression also exposed that the reference `World.from_state()`
shares some input dictionaries (e.g. learned values) with its caller. The verified
reference is left unchanged. The new experimental restoration boundary will copy
its input before calling that constructor, so retained experimental snapshots
cannot be mutated by later restored-world operations. This is an ownership fix,
not a change to decisions, randomness or experimental outcomes.
