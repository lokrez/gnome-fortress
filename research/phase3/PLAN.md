# Phase 3 execution plan

Reference: phase2-verified, 5efc9b1bfdd8d49a13aefd4e9256e6c1e87c024f.
All historical research files, tags, datasets and tests remain preserved.

1. Freeze exact reference modules. Profile young and mature query/save work before
   optimizing, including a 100,000-tick archive. Record CPU, wall and RSS.
2. Evaluate a living-agent index. Prefer the smallest index that removes retained
   corpse scans; preserve insertion order, awake filtering and Manhattan distance.
   Dynamic position references must preserve direct coordinate interventions.
3. Remove redundant full-state/deep serialization from saving. Evaluate content-
   checked incremental rows and append-only events in the existing queryable schema.
   Use one SQLite transaction, robust lineage checks and legacy loading. Never
   assume archived records are unchanged without checking their contents.
4. Keep the observer responsive during saving by freezing simulation at a complete
   tick while a writer thread runs; render/controls continue. No concurrent world
   mutation or asynchronous decision execution. Paused loops must sleep. Add only
   operational CLI pacing/statistics needed for background runs.
5. Require exact full-state, RNG and event equality against frozen Phase 2 at
   multiple boundaries, fresh seeds and mature snapshots. Test rollback, abrupt
   interrupted writes, corruption, legacy loading and resumed continuation.
6. Run all 52 historical tests unchanged and focused Phase 3 regressions. Benchmark
   sequential fresh processes before/after; profile again. Preserve history file
   hashes, document limits, package evidence, commit and tag verified work.

No behavioral changes, slot increase, social learning or new gameplay.

## Completed verification

All six steps completed. Ten accepted fresh-process cases matched at all four
fingerprint boundaries; 16 direct mature checks agreed. All 72 tests passed,
including the unchanged 52 historical tests. All 72 published archives loaded
and matched original digests; historical bytes and tags are unchanged. Final
observer measurements and source refinements are recorded separately from
headless timings. Report, plots, bundle and checksums publish this evidence.
