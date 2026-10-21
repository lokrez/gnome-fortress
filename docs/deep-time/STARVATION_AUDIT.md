# What a recorded starvation death establishes

The engine updates biology before scheduling. Hunger increases by 1 and thirst by
2 every tick. Hunger >100 costs 2 health; thirst >100 costs 3. If health reaches
zero during biology the recorded cause is dehydration when thirst >100, otherwise
starvation. Both needs can contribute, and preceding hazard damage can reduce the
remaining health. These cause labels do not prove an exclusive causal mechanism.

Only assigned, living, awake individuals execute the ordered decision procedure.
Drinking (thirst >=30 with adjacent water) precedes eating (hunger >=30 and food
>=10 on the current tile). Sleeping is excluded at hunger >=80 or thirst >=75;
existing sleepers wake early at hunger or thirst >=85 during biology. Thus a
hungry scheduled agent with edible food can drink first. An unscheduled individual
cannot eat just because global stocks are abundant.

Movement considers the nearest observable edible tiles and water by Manhattan
distance, not a global path planner. A visible edible tile is not necessarily
reachable by a short legal route. Food direction competes with water direction,
visits, hazards, learning and gated social terms. This study records real executed
actions; it does not infer counterfactual candidate scores for unobserved agents.

The research monitor samples hunger >=80 after biology and before any scheduled
decisions. Availability at this boundary can change before a later gnome acts;
actual decision-local stock is measured separately immediately before its action.
Deaths before scheduling have no opportunity in that tick. Empty-region samples
are taken every 10 ticks after regeneration/before decisions. These are explicit
sampling boundaries, not every-frame resource maps.

Retained observations: aggregate counters; per-living-agent exposure counters
retired on death; at most 128 example deaths per seed; 16 recent positions per
living individual; fixed map-size food accumulators. A recent-position revisit
is not by itself proof of inefficiency. Trait bands and prior injury are
observational covariates, not randomized interventions.
