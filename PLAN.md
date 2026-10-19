# Prototype implementation plan

1. Inspect host and create an independent repository. **Done.**
2. Build a headless, seeded integer-tick world and 60 persistent founders.
3. Add local decisions, biological needs, episodic consequences and learned associations,
   directional relationships, reproduction, permanent death and the 60-slot scheduler.
4. Add transactional SQLite snapshots, replay digests and command-line execution.
5. Add a Pygame observer with inspection, pause and speed controls.
6. Verify replay, checkpoint continuation, lifecycle, scheduling, measurable memory effects,
   accounting, and a prolonged accelerated run. Record actual measurements.
7. Document architecture, scientific boundaries, running instructions and next experiment.

Scope: one local simulator; no services, LLMs, civilization systems or game framework.

## Completion

All seven steps are complete. The smallest core was smoke-tested first, then extended
with lifecycle, learning, persistence and observation. Final verification: 27 tests
passed, including the 20,100-tick endurance/continuation check. See VERIFICATION.md
for measured results. The repository remains independent and has no remote services.
