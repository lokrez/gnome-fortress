# Phase 4B inspection and implementation plan

References: Phase 3 2f5213c; Phase 4A e8eac96. Preserve all their package files
and published datasets. New module and research harness only; no default changes.

Inspection findings:
- Phase 4A rejects a sender without firsthand_count: multihop does not work.
- move:hazard is an action/terrain-class association, not a location or statement.
- Values are EMA score weights, not certainty probabilities. Existing transmission
  halves the sender value then applies 1/4 learning weight with floor division.
- last_source/counters are insufficient to reconstruct a chain. Repetition can
  strengthen values. Core significant event history is unbounded by design.

Implementation:
1. Separate TelephoneWorld/config. Off, direct, multihop, masked conditions.
   Natural operation continues to piggyback on existing social decisions. Source
   provenance is self-contained: grounding experience + bounded participant path
   + at most seven receipt records (maximum eight participants). One social
   acquisition per association; no repeated reinforcement or merging of roots.
   Retain only 128 telephone audit entries and one latest movement record/agent;
   do not append every new telephone interaction to core world event history.
2. Three-agent harness with 60 founding records, three alive. A really moves into
   hazard. At tick 1 prescribe A's local contact action and B's ordinary safe
   movement; C sleeps. At tick 2 prescribe B's local contact and C's ordinary
   movement. These are explicitly controlled scheduled interventions, not claims
   of naturally emerging dialogue. Biology and movement call the original code.
3. Matched seeds 1–64, all five controls: individual, direct, multihop, masked,
   and an irrelevant-content harness that changes only the forwarded terrain key
   to move:grass. False/irrelevant injection exists only in the harness. Keep
   all meetings, scheduled opportunities and RNG states before C's choice matched.
   Verify C had no firsthand exposure and that a delivered chain changed its
   actual movement. Report absent/negative results without tuning the fixture.
4. Keep original half/quarter attenuation (no stochastic jitter). Report source,
   packet and recipient values at each hop, including floor-division bias.
5. Separate checksummed atomic experimental checkpoints, explicit harness loader,
   read-only companion inspector for C's proof and recorded decision. Test reload
   mid-chain, missing/dead/asleep/nonlocal sources, duplicates, loops, hop limits,
   rollback, proof corruption and bounded repeated-message storage.
6. Focused tests first; then relevant fast regressions and exact reference checks.
   Small isolated-process timing/memory measurements and a duplicate-stress test.
   No endurance run or historical archive campaign. Report uncertainty/limitations
   of this engineered chain and noisy short performance samples.

Provenance bounds are per retained identity/association, not a claim that the
whole persistent population/history uses constant memory. A new physical hazard
experience can ground a fresh root; its EMA may retain earlier social influence,
which must be labeled rather than counted as wholly independent evidence.

Scheduler inspection refinement: after tick 1 ends with cursor B, tick 2 schedules
C before A/B. Do not reset the cursor to force the desired story. C therefore
waits in tick 2, B contacts C later that tick, and C makes its scored movement in
tick 3. The controlled trial has eight scheduled decisions across three ticks,
including deliberate waits; it keeps the original scheduler ordering unchanged.
