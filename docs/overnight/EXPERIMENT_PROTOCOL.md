# Predeclared bounded matched-world protocol

Written before campaign outcomes. Seeds **1, 2, 3**; horizon **3,000 complete ticks**.
Five conditions, each independently replayed with full state/event/RNG equality.
Every primary run saves at tick 250, reloads, verifies exact state and continues.
All actions are request ticks (activation is request + 1, before food pulse).

Target criteria, evaluated from the initial map before outcomes:
- Land center: initial grass/forest nearest map center by Manhattan distance,
  ties row then column. Radius 2 for terrain actions; no outcome-based targeting.
- Spring: first row-major initial rock with any traversable neighbor. Radius 0.
- Rain radius 5 and Drought radius 3 use the same land center.

| Condition | Fixed request schedule |
|---|---|
| A untouched | none |
| B fractured | Rupture at 99 |
| C restored | Rupture 99, Rewild 399 |
| D freshwater | Wellspring 199 |
| E combined | Rain 49 duration 300; Rupture 99; Drought 249 duration 200; Rewild 399; Wellspring 499 |

Metrics: full ordered requests/transitions, final terrain composition/food, living,
individuals born (founders included), offspring births, deaths by recorded cause,
hazard entries, coordinate/tick-grounded entries on currently Rupture-transformed
hazard, full canonical and RNG digest, exact midpoint/replay checks, primary wall
time/TPS, worker CPU and process peak RSS. Separate worker per condition so RSS is
a per-process measurement including verification/replay, not simulation-only RAM.

A compares complete World state with the preserved Phase 3 implementation through
3,000 ticks. All conditions compare against untouched state before their first
accepted request. Replay includes a fresh independent initial world and identical
requests; post-midpoint continuation uses the loaded checkpoint. No controlled
population, forced decisions or injected biological events.

First benchmark combined seed 1 at 500 ticks. Estimate full campaign using that
measurement plus a conservative allowance for larger populations/save/replay.
Run only the bounded campaign; no indefinite or historical archive campaign.
One 10,000-tick combined operational run is optional after earlier gates pass,
with identical input schedule and replay/save checks, clearly separate from the
predeclared 15 primary comparisons. Do not tune targets after seeing outcomes.

Finite matched-world differences are observations under these rules, not survival
benefit estimates or proof about individual causal deaths. Once trajectories
and choices diverge, RNG consumption can diverge despite matched initial seeds.
Hazard coordinate provenance does not establish that an agent would otherwise
have survived. No communication, culture or intelligence experiment is included.
