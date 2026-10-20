# Phase 4C preregistered protocol

Declared before Phase 4C outcome execution, 2026-10-20.
References: Phase 4B 2644229; documentation be50c49. Preserve all existing
application modules, tests, tags and research data. New research files only.

## A. Original 64-seed C-only ablation

Seeds 1–64, unchanged ThreeGnomesWorld multihop through tick 2. Restore its exact
state for an ordinary tick-3 decision and a matched C-only readout ablation.
Capture actual candidates/scores, actor state, full state/RNG hashes immediately
before the original movement choice. Suppress hazard .get only when called by
World.move; keep stored associations and subsequent firsthand learning intact.
Reject ablation if hazard provenance is mixed (firsthand_count and social_count
both positive). Record every seed, selected coordinates/terrain, acquired value,
firsthand count, maximizer sets, changed position and avoided hazard. Explain
unchanged choices separately from lack of receipt or lack of applicable terrain.

## B. Fixed strength/preference matrix

Seeds: 1,2,3,4 (fixed tie samples, not a population-effect estimate).
Source scores: -64,-32,-16,-8,-4,-2,-1,0 (valid [-100,100] association units).
Depths: 1,2,3,7 transmissions (within eight participants).
Hazard-minus-best-safe baseline score margins:
-8,-4,-2,-1,0,1,2,4,8,16,32,50.
Arithmetic: original floor; truncation toward zero; nearest with ties away from
zero, each applied separately at /2 and /4. No main-code arithmetic changes.
Controls: individual, direct-only, multihop, masked, irrelevant-at-final-hop,
and C-only readout ablation. Total: 4*8*4*12*3*6 = 27,648 decisions.

This is an isolated synthetic source-strength intervention, not a claim that all
these weak/strong first-person estimates occur naturally. A first makes a real
hazard encounter; retain that actual episode/value separately from the imposed
source readout. A then makes a real safe transit. Arrange recipients along an
adjacent walkable line, with a unique grounded source and maximum depth seven.
Contacts are prescribed local interventions, not autonomous social choices.

Use one hazard candidate and three grass candidates at C at every depth. Set C's
curiosity and sociability to zero; no food/water targets. Generate negative
margins by inherited caution (-margin*5); zero by caution/visits zero. For positive
margins 1,2,4,8 give each safe tile one visit and caution=(8-margin)*5; for
16,32,50 use 2,4,7 visits and caution zero. All values are supported model fields.
These are prescribed grass preferences, not invented prior hazard experience.

Reuse the real movement function for score capture and actual selection. Match
RNG/state at the decision boundary; only the declared score content varies.
No source can send a nonnegative warning; reaching zero can stop later forwarding.
Masked carriers preserve opportunities without association content. Irrelevant
content assigns the final warning to move:grass, only in the research harness.
No physical/biological ticks are advanced in this decision-boundary matrix.
Its controlled contact/decision interventions are not scheduler throughput data.

Per row: contact/delivery status and reasons; acquired score each hop; pre/post
candidate scores; raw/RNG hashes; actual movement; firsthand status; score
applicability; changed maximizer set; baseline hazardous choice; actual position
change; hazard avoidance/increase. Distinguish attempted delivery, useful received
weight, candidate applicability, ranking relevance and actual behavior. Do not
call already-safe/irrelevant decisions failures of transmission.

## C. Arithmetic diagnostic

All signed source integers -100 through +100, all three arithmetic methods,
depths 1–7. This is a mathematical transfer-function table; positive/zero scores
are NOT admissible warning packets in the actual channel. Analyze sign symmetry,
zero, fixed point -1, strength loss and where arithmetic alone changes choices.

## D. Ordinary-world observational pilot

Seeds 1,2,3; 300 ticks each; individual/direct/multihop/masked TelephoneWorlds.
No map/trait/contact interventions, 60 founders and 60 slots. No irrelevant-content
injection. Total 12 worlds, 3,600 ticks, with one exact instrumented replay each.
Modest horizon based on prior ~0.6 s/200-tick baseline and extra measurement cost;
time a 50-tick sample first and report estimates before the full pilot. Keep this
pilot separate from the controlled matrix; do not extend it because results are
uninteresting or propagation is absent.

Count genuine existing social pairs, channel attempts, spatial opportunities,
direct/multihop receipts, rejections, recipient movement opportunities, adjacent
hazard/safe choices, changed rankings, coupled-RNG position changes and hazard
avoidance. Only ablate pure-social associations; count mixed states as excluded.
Coupled choices at an actual boundary are immediate counterfactuals, not later
matched trajectories. Track unused receipts, never-personally-verified receipts,
hear-episode eviction, association retention, proof replacement and deaths.
These categories overlap where stated; episode eviction is not knowledge loss.

Use aggregate counters and one usage record per retained recipient identity;
cap diagnostic examples at eight/world. No additional per-tick/per-interaction
world history. Original engine history/identities keep their existing semantics.

## Verification and stopping

Focused tests first; exact replay of all controlled result rows and all pilot
worlds/metrics; source hashes against reference; relevant fast regressions,
excluding the prolonged unattended test and historical archives. Test original
score capture/tie behavior, rounding/signs/zero, competing preferences, provenance,
mixed-origin rejection, nonmutation and bounded diagnostics. Keep original
movement and all pre-existing modules untouched. Stream compressed full matrix
CSV plus plain aggregate CSV/JSON. Timing fields are excluded from replay checks.

Do not tune the matrix after results. Any change must be logged as correction or
exploratory amendment before rerunning affected results. No Phase 4D or long
endurance campaign is authorized by this protocol.
