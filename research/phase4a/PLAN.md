# Phase 4A: first conversation — implementation and experiment plan

Reference: phase3-verified (2f5213c), observatory milestone 8a5971f.

1. Keep engine/model/storage/runtime/Pygame unchanged. Add an experimental World
   subclass, explicit condition configuration and separate checked SQLite format.
   Disabled communication must reproduce the reference engine state exactly.
2. Piggyback on actual existing `social` interactions: a sender with firsthand
   `move:hazard` knowledge can transmit that one association to its actual nearby
   partner, provided the partner has no firsthand hazard experience. No new
   random draws, interactions, decision slots or biological rules. Source-only
   firsthand teaching; no forwarding or parent-to-child inheritance of knowledge.
3. Compare individual learning, communication, and masked-message sham. All use
   the same social-interaction rule/cost. Attenuate source value by half and update
   recipient by the existing 1/4 learning weight. A distinct `hear` Episode,
   provenance counters and event distinguish transmission from physical experience.
   Association strength is not a calibrated probability or certainty estimate.
4. Test a two-living-gnome controlled arena with an actual forced firsthand hazard
   encounter by the sender, then one scheduled tick. Across seeds 1–64 compare all
   three conditions, including absent contact. No selection on successful lessons.
   Measure changed movement before recipient firsthand exposure, plus RNG/state
   comparisons of sham vs individual. Find one illustrative successful seed only
   after reporting the complete probe cohort.
5. Run a short pilot of seeds 1–8 for 500 ticks/condition, after a 200-tick timing
   sample. Report opportunities/messages, hazard encounters, deaths, births and
   time spent in communication hooks. This is not a survival-benefit campaign.
6. Extend the observatory with an explicit living-descendant roster, preserving
   founder records and founder default. Display real provenance and communication
   events; permit experimental worlds/checkpoints only through explicit flags.
7. Fast targeted tests first, then relevant regressions. Verify experimental
   save/load and exact replay including provenance/RNG/events, and frozen-reference
   equivalence with communication off. No long endurance/archive campaign.

Exact matching is expected for sham vs individual behavioral states/RNG, despite
extra sham records. Communication can change movement, then encounters and RNG
consumption; matched initial seeds do not imply matched later random draws.
A successful engineered transfer probe establishes mechanism capability only,
not naturally emerging culture or a population survival benefit.
