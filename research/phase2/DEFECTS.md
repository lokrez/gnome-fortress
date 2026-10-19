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

Late-window export defect, identified before the supplement ran:

- The optional production-save probe adds two fields to just one row, whereas
  the shared CSV writer takes its columns from the first row. Export would reject
  the extra fields after timing completed. Correction: declare both optional
  fields as null on every timing row before populating the measured row. This
  changes only the new supplement's output schema, not any campaign or rules.

Measured operating limitation, no correction applied:

- The ordinary production `storage.save` call on the seed-1 world at tick
  100,200 took 18.007 seconds to a fresh probe file in the quiet supplement.
  The observer invokes saving synchronously on its event loop. This can cause
  long visible pauses even when headless simulation exceeds the target tick rate.
  Existing-file overwrite latency and mature desktop rendering were not measured.
  Keep this separate from logical simulation correctness and from the more
  expensive scientific checkpoint fork/replay verification. No save or viewer
  behavior is modified in Phase 2.
