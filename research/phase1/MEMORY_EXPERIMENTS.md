# Controlled memory experiments (designed, not run as a new population treatment)

The ten Phase 1 worlds all use baseline memory-enabled rules. The existing 100-pair
unit experiment was rerun with the 27-test suite: it verifies a local mechanism,
not a whole-population survival benefit. The following designs are the next work.

## A. Matched one-decision mechanism experiment

Use saved snapshots from an independent, fixed collection of seeds 1001–1030, at
fixed ticks 500, 1000, 2000 and 5000. Before inspecting outcomes, define eligibility:
an alive, awake agent with at least one negative movement association and at least
two passable neighboring cells. Clone the COMPLETE state, including RNG. In one
copy preserve all state; in the other mask only `move:*` associations immediately
before that agent's decision. Do not erase visits, episodes, needs, traits, peers,
terrain, relationships or food. Execute the same one decision in each clone using
the same RNG state. Never feed either result back into the source trajectory.

Record: chosen action/cell, hazard entry, resource gain, expected score difference,
state digest before the intervention, identity, seed and tick. Report the denominator
of all eligible agent-snapshots, including pairs whose choice is unchanged. The
single-step comparison holds local conditions constant. It does not estimate
long-term survival and repeated snapshots of one lineage are not independent agents.
Use seed-level paired differences as the independent replication unit.

## B. Whole-population association ablation

Pre-register seeds 1001–1030 and horizon 20,000 ticks. Pair baseline-enabled and
association-disabled worlds initialized from the exact same full initial snapshot.
Disable movement-association influence for ALL agents, including descendants, by
clearing `move:*` learned associations immediately before each own decision in an
external treatment subclass. Retain visit counts, episodes, relationship values,
traits, sensing, decision priorities, scheduling and all random rules. Episodes can
still record consequences; cleared associations never affect a subsequent choice.
Call this **movement-association disabled**, not “all memory removed.” Never alter
Phase 0 source files or silently mix treatment data with the ten observational runs.
Verify the treatment adapter against exact one-decision fixtures before launching.

Primary outcome: hazard entries per 1,000 executed own decisions. Secondary outcomes:
hazard and recorded need-death counts per 1,000 agent-ticks, final population,
parenthood per 1,000 agent-ticks, and lifespan of all newborns born by tick 17,000.
Report birth/death totals as well as normalized rates: survival changes population
and decision exposure. A failed or extinct run stays in the analysis.

Use one enabled-minus-disabled result per seed. Report all 30 pairs, median/mean
paired differences and seed-level uncertainty (e.g. a fixed-seed bootstrap of the
30 pairs). Do not use thousands of related agents as independent replicates. State
all secondary endpoints and account for exploratory multiple comparisons.

Matched initial seeds are not matched future random shocks. Different choices can
consume different RNG draws, and subsequent reproduction changes eligibility and
population. Density, exposure and resource competition are outcomes/mediators of
this intervention; they cannot simultaneously be fixed in the whole-world test.
Keep the existing RNG implementation intact. Separate random streams would define
a new rule version and require separate verification.

## C. Separate visit memory from associative memory

If the scientific question means ALL decision-relevant memory, pre-register a later
2x2 study: associative readout enabled/disabled × visit-penalty readout enabled/
disabled. Keep history collection available in all four treatments. Specify exactly
which score term is masked, without changing sensing, need priorities or RNG. This
requires a carefully tested experimental adapter and is not implemented in Phase 1.
Merely erasing the 64 episodic records does not disable current learned behavior,
since the policy reads the learned table and visits rather than replaying episodes.

## Recommendation

Run experiment A first to validate the intervention on natural states, then B to ask
whether movement associations reduce hazardous exposure or improve survival in the
crowded ecosystem. The observed crowding should be measured as a mediator, not
“fixed” by increasing decision slots to obtain a preferred result. Separately extend
unchanged baseline seeds to 100,000 ticks before claiming ecological stationarity.
