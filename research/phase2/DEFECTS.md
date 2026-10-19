# Phase 2 defect and limitation log

Before implementation, 2026-10-19:

- Baseline capacity is a module constant used by construction, scheduling and
  validation. Non-60 experiment checkpoints therefore require a matching external
  configuration when loading. Ordinary 60-slot CLI behavior must remain unchanged.
- ru_maxrss is a process high-water mark. Reusing workers would contaminate per-run
  peak-RSS comparisons. Performance runs must use fresh child processes.
- Phase 1's generic 17,000 birth cutoff and “all complete” assertion are valid only
  at a 20,000 horizon. Extended-run lifespan cohorts need horizon-3,000 instead.
- Phase 1's terminal cause labels and end-of-tick slot occupancy interpretation
  limitations remain; no original behavior has been fixed or changed.

Pilot defect, before correction:

- The new Phase 2 runner used the same Counter key for event kind `hazard` and
  terminal death cause `hazard`, double-counting encounter totals when a hazard
  killed an agent. Both 1,000-tick pilots failed the independent per-agent hazard
  reconciliation assertion. No pilot outcome was accepted and no campaign had
  launched. Correction: namespace all death-cause counters with `cause:`; preserve
  both failed pilot directories/logs, add a focused regression, and rerun pilots.
  This affects only new telemetry, not core state, random draws or baseline rules.
