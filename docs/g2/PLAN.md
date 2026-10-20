# G2 plan

Initial checkout clean; main is accepted G1 597b0eb9bfcbee438c1959c6a73b1b3591511358.
No local or remote g1-verified tag existed; annotated tag created at that exact commit.

1. Document precisely three future release modes, shared metadata/policies and
   legacy treatment. Implement no selector, mode metadata, migration or progression.
2. Add presentation-only helpers: incremental index of real meaningful events,
   cached map resource totals, derived overlap/expiry/ledger views and read-only
   individual inspection. Rebuild once on load; keep all UI state out of checkpoints.
3. Upgrade GodObserver with world summary, two sidebar tabs (individual/powers),
   scrollable event feed below the map, live intervention statuses and clear gnome
   markers. Keep inputs, pacing, worker semantics and launcher unchanged.
4. First targeted tests, then relevant fast suite. Compare actual G1-generated
   saves and recorded intervention schedules with G2 continuation and inspect
   rendering/RNG invariance. Do not run historical archives or endurance studies.
5. Capture the real Pygame build on X11, measure bounded presentation costs and
   audit unchanged science/engine/storage. Document scripted versus human checks.
   Commit and push G2 and the new annotated baseline tag; stop.

G1 presentation gaps documented before implementation: the request notice remains
static after activation/expiration; inspection omits sleeping state, parents and
recent memories; resource ledgers and world deaths/food are not shown. These are
viewer deficiencies, not evidence of a simulation defect. No G1 biology, powers,
scheduler, save format or research behavior needs correction.
