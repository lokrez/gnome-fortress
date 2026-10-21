# Production inheritance audit

Source remains `72a1017:gnome_fortress/engine.py`; no experimental arithmetic is
installed in production. Relevant locations: founder traits lines 44–47;
biology 98–120; ordered decisions 173–216; inheritance 196–198;
movement scoring 223–245.

Founders draw each trait independently as a uniform integer 20..80. Each child
gets `clamp((parent_a + parent_b)//2 + randint(-10,10), 0, 100)` independently for
each trait. The pre-clamp mutation expectation is zero. Parent averaging reduces
within-population variance; finite sampling creates genetic drift. Floor rounding
subtracts 0.5 exactly when the parent sum is odd. It has no error for even sums.
Approximately half odd sums would yield approximately -0.25 per birth, but parity
is endogenous and must be measured. Clamping counters downward movement near zero
and upward movement near 100. Repeated averaging, floor bias, mutation and bounds
can change a population mean without ecological selection.

Parents are spatial, awake, eligible local individuals, checked in stable order.
A scheduled eligible agent tests eligible neighbors until the first reproduction
success. The probability for each tested pair is
`floor((fertility_a + fertility_b)/3)/1000`. Thus a well-mixed pair-weighting toy
isolates a genuine probability term, but does not reproduce sequential attempts,
spatial encounters, scheduling, cooldowns, age, health or parental need costs.
There is no modeled biological sex. No simulated marriage is inferred.

Trait connections:

| Trait | Actual connection | Important limits |
|---|---|---|
| Fertility | Pair reproduction probability | Spatial/needs/cooldown eligibility still required |
| Stamina | Old-age threshold `1800 + 12*stamina` | Does not directly improve movement or starvation resistance |
| Caution | Hazard candidate penalty `caution//5` | Only movement candidates; learned association is separate |
| Curiosity | Unvisited-tile bonus `curiosity//4` | No effect on already-visited candidates |
| Vision | Manhattan sensory radius `3 + vision//25` | Values 0..24 all have radius 3 |
| Sociability | Social probability/reward and peer movement term | Needs gates and integer thresholds; no faction system |

All six values have some active connection. Several integer plateaus mean a
changing number need not change an evaluated outcome. Numeric relationships are
updated but do not define friendship, occupations or global partner preference.
Trait covariance, spatial exposure and differential survival can confound
observational full-ecology associations. A toy reproduction-weighting comparison
cannot identify the player's precise historical selection coefficients.

The science report must separate mathematical drift, differential reproduction,
differential survival and covariance. The production trait rule is not changed
because its rounding might produce an inconvenient result.
