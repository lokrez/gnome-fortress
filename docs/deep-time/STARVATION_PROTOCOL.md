# Starvation study — prospective bounded instrumentation

Use the same declared fresh ecology seeds/horizon as the inheritance ecology
pilot, keeping biology, reproduction, movement, RNG and 60 slots unchanged.
No reconstruction of the player's old candidate scores is possible or attempted.

Experiment-only wrappers observe actual scheduling, executed decisions and deaths.
Counters summarize hungry (hunger>=80, separate >=100) living-agent tick exposures,
awake/asleep status, actual assigned opportunities, local edible stock (>=10),
and edible tiles within configured sensory radius. Potential observability is
not claimed to mean that an earlier action branch actually evaluated those tiles.
Actual decision actions are distinguished from biology and unassigned ticks.

At death record real final need/health/location, local edible availability and
preceding scheduling/feeding counters. Keep bounded example records (maximum 128),
aggregate per-seed counters and fixed-size tile accumulators; no permanent biographies
or full-population scoring trace. Retire per-living-agent counters on death.
Incrementally inspect only appended hazard/sleep/wake events.

Questions: availability vs action opportunity; edible threshold; food depletion
regions; fatigue/sleep; actual eat/move/drink priorities; prior hazard exposure.
Trait/region/injury correlations are observational and not causal.

Controlled feasibility probe: compare matched observational instrumentation on/off
for seed 1 to prove exact state/RNG equality. A strictly experimental paired
higher-slot or trait intervention may be proposed after these observations, but
is not necessary to claim observational evidence and will not be silently added.
Report unresolved causal questions rather than reinterpret correlation as proof.

Before launching: also require an uninstrumented 10,000-tick replay of seed 1 to
match the complete instrumented canonical digest, not only the short pilot.
This adds one ordinary-world run to the runtime estimate. Birth arithmetic
summaries use recorded parent and child traits; the original mutation sample is
not stored, so `child - floor(parent average)` is mutation **plus clamping**, not
an inferred exact random roll. Death examples are first occurrences, not curated
for dramatic outcomes.
