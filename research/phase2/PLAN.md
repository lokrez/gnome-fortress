# Phase 2 execution plan

Preserve phase0-verified=f32c1a6 and phase1-verified=232dd30, all historical
research files, core source and original tests. New controls live under research/.

1. Review Phase 1; register endpoints and controls before outcomes. DONE.
2. Implement process-isolated capacity configuration and association readout
   masking. Verify enabled neutrality, strict masking scope, normal association
   updates, context restoration, persistence/replay and capacity boundaries.
3. Pilot mature baseline throughput, capacity throughput, memory use and cProfile.
   Report measured workload estimates before launching full campaigns. No
   optimization before profiling. Adapt benchmark horizon if the pilot shows
   unacceptable cost; record any such decision before observing final outcomes.
4. B: run headless capacity benchmarks sequentially, without the scientific
   campaigns competing for CPU. Fixed seeds/horizons; include a scheduler-only
   fixed-population benchmark and full replay at every capacity. Measure biological
   consequences separately from performance. Do not change default 60.
5. A: at least 20 matched seed pairs, 20,000 ticks, exactly 60 slots, independent
   processes. Primary outcome is mean lifespan of all offspring born by tick
   17,000 (complete lifetimes). Safety endpoint is hazard encounters/1,000 own
   decisions. Retain all seeds including extinction. Seed-level enabled-minus-
   ablated differences, 95% paired bootstrap intervals (10,000 resamples, analysis
   seed 20261019), and full per-seed outcomes. Other endpoints are secondary.
6. C: unchanged 60-slot enabled rules, seeds 1,2,3 to tick 100,000, continuing the
   verified Phase 1 tick-20,000 snapshots if this saves redundant work. Report the
   reused prefix explicitly. Resource, generational and scheduler samples; exact
   event-derived births/deaths/extinction. Mid/late checkpoint continuation checks.
7. Run the original 27 tests, six Phase 1 research tests and focused Phase 2 tests.
   Confirm baseline files and historical datasets are byte-unchanged. Reconcile
   telemetry, checkpoints and full replay checks. Analyze, plot and document limits.
8. Package raw CSV/JSON, code, plots, logs, checksums and report; commit verified
   work. No services, GPU/LLM inference, visual redesign or new simulation behaviors.

## Progress

Controls passed 16 initial tests; a namespace-collision regression passed after the
pilot telemetry failure was documented and corrected. Corrected pilots completed.
Pilot assessment and the uncontended B campaign are underway. Statistical analysis
is implemented before A outcomes; it uses world-seed paired resampling, not agents.
