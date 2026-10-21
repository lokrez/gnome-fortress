# G8B implementation protocol

1. Keep decide, move, remember, random calls and scoring expressions unchanged.
   Add an optional tick-boundary bridge to an external weak-key registry.
2. Observe only one identity. Capture biology before/after separately, then wrap
   only that identity's real decision execution with a short-lived Python trace.
   Read real execution locals at movement/remember returns and real branch lines;
   never replay the algorithm or sample randomness for explanations.
   Restore the previous tracer, refuse competing tracing rather than replace it,
   and isolate observation failures. No user callbacks or mutable world objects
   are exposed in records. This approach trades selected-decision trace cost for
   a particularly small engine change and an unchanged decision implementation.
3. Keep 128 tick observations (including explicit no-slot records), at most 128
   decisions, and value-only bounded event/peer evidence. Switching identity
   discards the old trace. Death preserves records. No checkpoint fields.
4. Add an eighth journal tab (F4), opt-in recording, chronological browsing,
   readable rule/outcome summary and expandable factual detail. Existing controls
   and pixel art remain unchanged. One-step still means a complete world tick.
5. First verify exact behavior against the accepted engine, including all five
   powers, all action branches, biology death and snapshot continuation. Then UI,
   focused failure tests and the full fast regression suite.
6. Collect natural cases, real application captures with matching JSON traces,
   and selected-observation/Chronicle performance using isolated generated worlds.
   Report tracing limitations, startup costs and pending human playtesting.

Predeclared outcomes: exact canonical and RNG equality is mandatory. Candidate
scores must be execution locals; learning values must bracket actual remember.
Report totals first; contribution decomposition is deferred if it would duplicate
arithmetic. No survival-benefit claim is made. No owner's save is accessed.
