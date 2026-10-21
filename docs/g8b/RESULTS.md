# G8B — A Life Observed

Accepted baseline: `bf6e5568056e75f07cd7b9d468a592fc5e5abf6f`.

## Delivered

The existing terrain-game launcher now includes selected-gnome decision
observation in the parchment journal. **F4** opens **Acts F4**; **U / Observe U**
records future tick evidence. Space pauses, period advances one full tick,
Older/Newer or brackets browse, Latest follows new records, and wheel scrolls.
More detail exposes executed conditions, actual random samples, directional peer
changes and real event references. Center, Follow C and Life F3 reuse existing
navigation; Family remains available. The world and all powers continue running.

The journal distinguishes biology, actual scheduled decisions, immediate action
consequences and tick-end state. Sleeping/no-slot ticks are explicitly not new
choices. Movement displays executed candidate totals, the maximum, chosen
position, ties and learned contribution. Association changes bracket the actual
remember call. A lethal movement remains movement followed by recorded death;
a biological death has no fabricated final action.

Records are optional, value-only and session-local, bounded to 128 recent ticks.
Switching individuals stops/discards them; death preserves them. Checkpoints do
not contain past explanations, and loading never reconstructs candidate scores.
Agent episodic memory remains capped at 64. No new permanent biography archive,
objective events, simulation rules, traits, powers or external services exist.

## How it is truthful

`World.decide`, `move`, `remember`, biology, schedule and every other engine method
except `step` have identical ASTs to the accepted implementation. The tick loop
adds an optional external observer bridge. A short-lived owner-thread Python
execution trace reads the actual selected decision's branch lines and helper
return locals. It does not rerun rules, probability checks, scoring or tie breaks.
Movement/remember helpers require only call/return tracing. Collection exceptions
are contained; actual engine exceptions propagate without retry.

Source text/AST identifies executed conditions and call-site roles, not a second
rule implementation. Short-circuit subconditions are not claimed individually
true/false. Existing debugger/coverage tracing is preserved; detailed evidence is
then explicitly unavailable. Missing source/tracer refusal also fails explicitly.
This is a production-engine observation instrument, not a generic framework for
arbitrarily overridden experimental decision functions.

## Verification actually executed

- Focused G8B suite: **24 passed in 32.44 s**.
- Full fast suite: **306 passed in 206.86 s**, including all existing Saveguard,
  Chronicle, legacy storage, camera, art, gameplay and research-reference checks.
- Matched accepted / disabled / enabled replay: seeds 1 and 42, 500 ticks,
  14 checkpoints each. Complete canonical state and RNG agree, with all five
  powers, queued/active effects and terrain transitions. Reload from tick 20 and
  replayed subsequent inputs match exactly. Seed 1 had 52 births and one death;
  seed 42 had 52 births and zero deaths. These are replay coverage, not a power
  effectiveness comparison.
- Natural 2,050-tick reference comparison includes the observed founder's
  biological death at tick 2,048. No final decision is invented.
- Controlled fast fixtures cover drinking, eating, sleep, wait, tied/unique
  movement, negative learned values, social/reproduction peer effects, hazard
  death, biological death, unassigned slots, dense overlap, extinction,
  tracer/source/collection failures, bounded buffers, selection switching,
  eviction/browsing, rendering cadence and read-only navigation.
- Detached captures stay at T after the live world advances. Observed/unobserved
  ordinary snapshot bytes match; Chronicle restore and save/load preserve state,
  RNG and empty observation registry. Old readers/storage/format sources are
  unchanged, and the legacy tests pass. No archive migration was performed.
- Actual **X11 Pygame** replay captures assert screenshot identity/tick/record
  equality with naturally collected cases. A 4K borderless capture avoids the
  desktop window manager shrinking the test window. Normal gameplay remains
  windowed. This was scripted operation, **not human playtesting**.
- Actual generated 26k-world operation: observation, follow, feed, Advisor and
  Rain input while saving; warm capture/start **18.69 ms**, worker **9.06 s**;
  final exit save at 26,909 and exact reload continuation to 26,939.

Logs and hashes: [evidence](evidence/), [replay](evidence/replay.json),
[performance](PERFORMANCE.md), [case studies](CASE_STUDIES.md).
The long-run test and historical archive campaigns were not repeated.

## Limits and development findings

Only candidate totals and the learned term are decomposed, not every movement
component. A trace shows what the algorithm used; it does not establish that a
term was necessary for a choice or improved survival. No consciousness, motives,
feelings, social learning or civilization are claimed.

The 128-tick bound includes unscheduled ticks; a crowded world's window can
contain relatively few decisions. Detailed peer snapshots/random attempts cap at
64, with total counts retained. A debugger conflict yields incomplete evidence,
never a fictional explanation. Exported natural-case evidence is research output,
not an added gameplay biography feature.

Enabled tracing measured roughly 3–8% additional simulation time in short matched
probes. Rendering the detailed journal remained around 10 ms at 1280×720.
Warm Chronicle capture remains around 19 ms at 26k. A cold-start frame gap reached
154 ms and a pending-save gap 90 ms in the operational run. Cold-save/history
preparation limits remain; G8B does not claim to fix them. Human usability and
smoothness approval remain pending.

Development corrections: removed unnecessary tracing of helper lines; bounded
large-neighborhood evidence; fixed browsing after oldest-record eviction; used
ASCII arrows supported by the journal font. The preservation script briefly
reused a variable name and failed JSON export; it was fixed and rerun successfully.
No baseline biology/persistence defect required a behavioral change.

## Preservation

The owner process and its writer were inspected read-only; neither was opened,
signalled, suspended or stopped. Tests used fresh worlds, trusted generated
fixtures and temporary checkpoint paths. The owner's live save was not loaded.

`evidence/preservation.json` hashes the protected core/model/game/persistence,
Chronicle/Saveguard, camera/art and presentation files. All are identical to the
accepted baseline. Among preexisting tracked files, only `engine.py` (tick bridge),
`living_viewer.py` and `README.md` changed. Earlier datasets, reports, mode
contract, reference implementations and Git tags remain intact. Observation has
no checkpoint fields and no ownership/recovery changes.

## Reproduce / owner review

```bash
cd ~/gnome-fortress
.venv/bin/python -m pytest -q tests/test_decision_observation.py
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
.venv/bin/python -m research.g8b_audit
.venv/bin/python -m research.g8b_replay
.venv/bin/python -m research.g8b_cases
SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy .venv/bin/python -m research.g8b_capture
```

Performance/mature operation use **generated**, not player, fixtures:

```bash
.venv/bin/python -m research.g8a2_profile --fixtures /tmp/gnome-g8a2-generated-fixtures --out /tmp/g8b-fixture-generation.json
.venv/bin/python -m research.g8b_profile
.venv/bin/python -m research.g8b_memory
SDL_VIDEODRIVER=x11 SDL_AUDIODRIVER=dummy .venv/bin/python -m research.g8b_operation
```

The source generator uses seed 1 and the unchanged ordinary rules. These commands
are bounded but not instantaneous. Full Git history must include the accepted
baseline for the independent reference tests. No new dependencies were installed.

Launch is unchanged:

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_world
```

Save and exit an existing game normally and wait for its terminal prompt before
relaunching this build. Do not start a second owner for the same checkpoint.
Review F4/U, pause/step, actual rule clarity and scrolling in your own playtest.
G8B stops here. No subsequent milestone is started.

See the milestone commit in `git log -1` and the delivery message for its final SHA.
