# Actual observed cases

Natural protocol: seeds 1 and 42, founders 1–8, 600-tick windows each;
plus seed 1 / founder 1 through death or 3,100 ticks. No modified cells,
needs, traits, randomness or scripted meetings. Each window starts a fresh
ordinary world. First qualifying examples are retained; no dramatic seed search.

Each `evidence/case-*.json` contains detached trace data, inherited traits, seed,
identity and tick. Running-build captures replay the same real input/tick history
and assert record equality before capture. Test-only synthetic branches are not
presented as natural cases.

| Seed / identity | Tick | Recorded evidence | Interpretation limit |
|---|---:|---|---|
| 1 / #00001 | 10 | Thirst 30, drinking selected; thirst became 0; `drink:water` 0 -> 15, reward 60. | Ordered threshold rule, not evidence of a subjective desire. |
| 1 / #00002 | 11 | Drinking selected. Curiosity 80, caution 51, sociability 46; real prestate in JSON. | Distinct traits do not establish their causal importance for this drinking event. |
| 1 / #00003 | 8 | Social interaction selected; inherited curiosity 23, caution 27, sociability 47; reward 4 and association 0 -> 1. | Numeric interaction, not friendship or intention. |
| 1 / #00001 | 20 | Hunger 30 and local grass food 40; eating selected, actual reward 40, hunger 30 -> 0. | Food consumed follows the existing rule, not optimization of all possible actions. |
| 1 / #00001 | 38 | Entered hazard (14,12); health 100 -> 76; reward -72; `move:hazard` 0 -> -18. | Actual injury and association update, not proof of useful learning. |
| 1 / #00001 | 41 | Hazard candidate (14,12) scored -56 including learned -18; forest (13,13) scored +18 and was selected. | The term contributed; this example does not show it was necessary to change the choice. |
| 1 / #00001 | 47 | Social encounter with #00046; outgoing value 0 -> 3, incoming 0 -> 2. | No reciprocal feelings are inferred. |
| 1 / #00001 | 65 | Fatigue 65, hunger 15, thirst 20; sleep selected, until tick 77. | Subsequent sleeping ticks are biology without decisions. |
| 1 / #00001 | 255 | Reproduced with #00034; child #00083 born; actual events 1182 and 1183. Both parents gained 20 hunger / 15 fatigue, cooldown 240, child counter +1. | Family is a biological fact, not a social organization. |
| 42 / #00005 | 11 | Drinking selected, association 0 -> 15. Traits include curiosity 44, caution 35, sociability 48. | A second environment/individual, not a statistical trait-effect study. |
| 1 / #00001 | 2048 | Old-age death during biology; no decision assigned; final recorded age 2232. | No invented final choice or last words. |

## A bounded longer observation

Founder #00001 was observed for 2,048 ticks, from initial recorded age 184
through biological death at age 2,232. The 3,100-tick limit was not reached
because recording stops at death. Counts: 534 movements, 106 drinking, 74
eating, 27 sleeping decisions, 17 social interactions, three reproduction
decisions, and 1,287 ticks without a decision slot. Three children were
recorded. These are executed actions, not continuous activities between ticks.

The interactive ring retains only the last 128 ticks, not this entire life.
The study script counts observations and exports selected cases as research
evidence; it adds no permanent gameplay biography or agent memory.
The full run table includes all 16 distinct seed/identity combinations.

Neither these cases nor their differences establish a survival advantage,
trait causality, conscious experience, social learning or culture.
