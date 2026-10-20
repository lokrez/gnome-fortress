# G1 implementation plan

Reference: Phase 4C 52374aa; research baselines and datasets remain intact.

1. Extract only the existing food-regeneration block into `World._regenerate_food`.
   Its default body and tick boundary remain identical. Verify full state/RNG/events
   against the preserved Phase 3 independent reference and inactive GameWorlds.
2. Add an opt-in GameWorld. Requests at completed tick t activate at t+1 and
   expire exclusively at t+1+duration. Euclidean integer circles clip to the map.
   Standard interval is 10 ticks, grass +4 / forest +8, capacity 100. Rain doubles
   those increments; Drought gives zero, never removes food. Rain does not stack;
   Drought wins overlaps; earliest ID of the winning type receives accounting credit.
   Retain all requests, exact boundaries, activation/expiration events and aggregate
   per-regeneration resource accounting. No agent rules or RNG draws are added.
3. Add distinct versioned `.g1.sqlite` SQLite snapshots with checksums, transactions,
   strict validation and refusal to write research paths or non-game databases.
   Load errors are fatal. This is manual-save prototype persistence, not Ironman.
4. Reuse Observer drawing conventions and controls through a separate game viewer
   and `python -m gnome_fortress.god_demo`. Add power buttons, targeting/preview,
   active feedback/history and extinction overlay. Background saving freezes ticks
   and intervention input; navigation remains available. Save on clean exit/signals.
5. Fast targeted tests first, then relevant fast regressions (no long-run/archive
   campaign). Test boundaries/overlaps/caps, repeated requests, invariant agent input,
   replay, active save/load, corrupt/interrupted checkpoints, read-only observation,
   extinction, shutdown and preservation of research files.
6. Fixed short demonstration: seed 1, 300 ticks, compare no power/Rain/Drought;
   request at tick 20, center (24,16), radius 8, duration 150. Record actual resource
   deltas and population/needs/deaths, not a scripted narrative. Capture the running
   Pygame build. Report limitations, commit separately, stop after G1.
