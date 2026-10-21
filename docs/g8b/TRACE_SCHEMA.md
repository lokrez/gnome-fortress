# Disposable observation schema

These are Python/JSON inspection values, **not a save-format extension**. A weak-key
registry associates a live world with one collector. The world has no observer
attribute, callback, trace field, new event, or new random state.

## Tick record

- `tick`, `identity`: stable simulation time and ID.
- `scheduled`: whether the actual decision invocation occurred.
- `biology_before`, `biology_after`: detached scalar state bracketing the biology
  phase. Regeneration/intervention activation precede this boundary.
- `biology_events`: actual appended wake/death events involving the identity,
  with indexes, ticks and copied details. No earlier history scan.
- `decision`: null if no slot; otherwise the execution evidence below.
- `tick_end`: state after other scheduled agents have also acted. It can differ
  from the subject's immediate decision outcome, e.g. another parent reproduces.
- `status`: scheduled, asleep, eligible without a slot, biological death, or missing.

State values contain position, age, health, needs, sleep deadline, alive/death
fields, cooldown, children and latest action. They contain no Agent references.

## Decision record

- `before`, `after`: immediate scalar state at invocation and return.
- `context`: actual local terrain and food before invocation.
- `action`: selected action, distinct from final `after.action`. A lethal hazard
  entry is movement followed by death, not a decision to die.
- `rule`: explanation of the selected ordered branch. This is not global utility.
- `checks`: conditions whose statement lines executed, original source text and
  whether their branch body was entered. An `and` expression short-circuits;
  absence of entry does not establish which subcondition failed. Source line
  locations are derived with AST, not duplicated threshold logic.
- `random_attempts`: actual `randrange` return samples and call-site role, bound,
  partner ID where available. No new samples are taken. At most 64 are retained;
  `random_attempt_count` reports the full number. These are eligible, actually
  attempted checks, not hypothetical rolls for ineligible rules.
- `movement`: null if not reached; otherwise actual `move` return locals:
  origin, passable candidate totals, maximum, chosen destination, tied maximum,
  whether the existing choice call occurred (also true for a unique best), and
  observed food/water/peer positions. Each candidate includes the learned terrain
  term actually used from the predecision associations. Other score components
  are not separately decomposed. The formula and integer floor operations are
  unchanged. No candidate table is reconstructed after a reload.
- `learning`: actual `remember` call reward, feature/key, previous/current value,
  and position. Zero reward is still an experience and may alter an association.
- `peers`: before/after state and directional relationship values for up to 64
  nearby peers; `nearby_count` gives the actual total. Large neighborhoods may
  omit a partner from detailed peer snapshots; objective interaction events still
  identify the actual partner/child. Peer changes bracket this one invocation.
- `events`: copied objective events appended by the executed decision, with exact
  zero-based indexes into the world event sequence. These are references to facts,
  not new simulation events. Existing decisions append at most a few such events.
- `complete`, `unavailable`: explicit failure/tracer-conflict reporting. Incomplete
  evidence is not formatted as a reconstructed explanation.

## Bounds, lifecycle and failure handling

The ring retains **128 complete-tick observations**, including no-slot ticks, so
there can be fewer than 128 decision records. No separate per-agent archives
accumulate. Switching selected identity stops and discards the old trace. Stop
preserves the current buffer; restarting the same identity resumes it. Death
preserves it and unregisters recording. Relaunch starts with no detailed history.
Oldest-entry eviction advances a pinned browser to the oldest retained tick.

Only the selected invocation uses `sys.settrace`, on its owner thread. Local line
tracing is limited to the real ordered decision function; movement/remember/nearby
helpers use call/return evidence. Unknown child frames are ignored. It neither
replaces methods nor supplies callbacks to plugins/UI. Collection exceptions are
contained; an engine exception still propagates and is never retried. A preexisting
Python debugger/coverage tracer is left installed and detailed evidence is marked
unavailable. Missing execution source or a refused tracer reports unavailability.

This observer is calibrated to the production World decision functions, not a
generic observer for arbitrary overridden experimental algorithms. AST-derived
locations reduce line-number fragility but do not remove that compatibility
boundary. Every future decision refactor needs renewed evidence tests.

The ring holds scalars, strings and bounded containers. It has no World, Agent,
frame, RNG, journal, or persistent episode references. Player observation is not
the gnome's capped 64-episode memory. It is not written to SQLite, Chronicle,
recovery journals or gameplay metadata. The JSON research evidence is explicitly
exported by the demonstration scripts and is not a gameplay subsystem.
