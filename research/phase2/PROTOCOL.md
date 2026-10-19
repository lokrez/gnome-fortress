# Phase 2 protocol — registered before full campaign

Runtime/rules pinned to phase0-verified=f32c1a6; Phase 1=232dd30.

A: seeds 1001–1020, both enabled and association-ablated, 20,000 ticks, 60 slots.
The paired states have identical initial world cells, agents, traits, needs and RNG.
Treatment changes ONLY learned movement-association READOUT during destination
scoring. Consequence updates, episodic records, visit counts, inherited caution,
perception, all other rules and RNG implementation are preserved. All offspring
receive the same treatment. This is not an ablation of visit/episodic memory.
Masking lives in an experiment-only adapter, not core source. Time/RSS measurements
never feed decisions. Seed matching does not couple future random draws.

Primary survival outcome: mean biological lifespan of all offspring born at or
before tick 17,000, with no minimum-decision survivor filter. The rule maximum
lifespan is 3,000, so this cohort has complete outcomes by 20,000. Co-primary safety
outcome: hazard entries/1,000 executed decisions. Secondary: final and late mean
population, deaths and cause-specific deaths/1,000 biological agent-ticks, offspring
births, per-agent reproduction, starvation, all completed-death lifespan summaries,
and censored survivors. Report each seed and enabled-minus-ablated effects. Use
10,000 paired seed-level bootstrap resamples, NumPy seed 20261019, percentile 95%
intervals; report paired t intervals as a sensitivity check. No independent-agent
p-values. Treat secondary intervals as exploratory, without familywise claims.

B: 60,120,240,480,960 slots. These are logical capacities in ONE serial world, not
threads. Fresh processes and sequential timing runs, no concurrent A/C campaign.
Provisional seeds 11,12,13 and horizon 3,000 ticks; select final affordable horizon
using a smaller pilot BEFORE final runs. Identical initialization except slot-array
length; record biological initial-state fingerprint. Record wall/CPU time, CPU as
percent of one logical core, fraction of 16 logical CPUs, peak RSS, scheduler timing,
executed/retained utilization, eligible opportunities, biological agent-ticks,
sleep/wake, population, births/deaths, hazard/starvation and reproduction. Time the
simulation loop separately from construction, digesting, validation and SQLite I/O.
Repeat a complete timing trajectory at each capacity to check determinism; separate
replay timings from primary throughput. Benchmark scheduler-only fixed awake/sleep/
dead synthetic populations to isolate selection overhead. Profile representative
live worlds before proposing optimizations. No permanent slot change or rule edits.

C: enabled 60 slots, seeds 1,2,3 to 100,000 ticks, optionally resume validated Phase 1
20,000-tick checkpoints. Preserve archived prefix and compare its final digest
before extension. Sample actual food stock and need pressure, births/deaths,
ancestry generation (founders=0, child=1+max(parent generations)), sleep/wake and
scheduler counts. Last windows and trends are descriptive, not permanent stability.
At mid/late boundaries verify exact save/load identity AND replay continuation.
Use complete original event history for lifetime/turnover totals; distinguish
prefix, measured extension and whole-horizon metrics. No forced extinction recovery.

All campaigns: sorted deterministic ordering, explicit seeded RNG, no interventions,
recorded configuration and code hashes. Keep completed and censored lifetimes
separate, and founders' initial ages separate from entry exposure. Death causes
are original terminal-rule labels, not independent damage attribution. No selection
of seeds/horizons based on favorable population outcomes. Document defects before
fixing affected behavior; none of these experiments authorize preferred outcomes.
