# Phase 4A — the first conversation

## Finding

This prototype demonstrates a narrow, programmed social-learning mechanism:
experience-derived association values can reach another individual through a
local interaction and change its subsequent movement before firsthand hazard
exposure. It does not demonstrate invented communication, culture, calibrated
beliefs, or long-term survival improvement.

All seven existing Phase 3 simulation package files remain byte-identical to
`phase3-verified` (`2f5213c23300e61330ea665bfb4789622bf38bc6`). The independent
Founders' Observatory baseline remains at `8a5971f`; its presentation/entry-point
code is extended here. Phase 0–3 tags and historical research datasets are intact.
See `environment-and-integrity.json` for exact references and source hashes.

## Smallest mechanism

`CommunicationWorld` subclasses the unchanged engine. `CommunicationConfig`
explicitly selects one condition:

| Condition | Existing individual learning/social interactions | Transmitted content |
| --- | --- | --- |
| individual | Unchanged | None |
| social | Unchanged | Attenuated `move:hazard` association |
| sham | Unchanged | Masked episode; no association information |

The normal application and observatory without `--communication` still construct
an ordinary World. Experimental individual mode tracks provenance but reproduces
the reference biological state, events, memory and RNG exactly.

After an existing `social` event, its actual sender may transmit to that event's
actual nearby partner. The sender must have firsthand hazard experience and a
negative `move:hazard` association. The receiver must be alive, awake, within
Manhattan distance one, and have no firsthand hazard experience. Experience-free
hearsay cannot be forwarded. An agent that hears first and later experiences a
hazard can subsequently teach: that sender's value may reflect both origins.
There is no global broadcast, new sensory ability, or cross-generation inheritance
of learned values. Children may receive messages through the same local rule.

For source value `s` and receiver's existing value `r`:

```
transmitted = s // 2
updated = clamp((3*r + transmitted) // 4, -100, 100)
```

This uses a weakened report and the existing EMA weight, with the engine's integer
floor arithmetic. It does not copy the teacher's full strength. Repeated lessons
can accumulate toward the attenuated value. These integers are association
strengths, **not probabilities of truth**; no perfect-certainty state is introduced.
Attenuation is a deliberately chosen experimental assumption, not a discovered
trust model. False/stale reports and calibrated reliability are not tested here.

Received episodes reuse the existing `Episode` structure with action `hear` and
feature `hazard` (or `masked` in sham); they do not masquerade as physical `move`
experiences. They share the existing latest-64 retention budget. An explicit
side table stores firsthand/social counts, last experience/message ticks and last
source for each association. Full retained communication events include sender,
receiver, source strength, attenuated report and before/after values. Original
hazard events retain evidence of physical encounters. Ordinary episodes retain
the existing finite-history limitations.

## Two-gnome demonstration and matched probes

```bash
cd ~/gnome-fortress
.venv/bin/python -m research.phase4a_demo
```

The arena is an explicit intervention, not a natural population outcome. It keeps
all 60 permanent founder records but kills 58 with cause `experiment_setup`,
leaving two living gnomes. It sets the same arena, needs, reproduction cooldowns,
and controlled traits in all conditions. A forced move through the real engine
produces an actual sender hazard consequence at tick zero; one normal scheduled
tick follows. Recipient caution/curiosity are zero and its two candidate tiles
otherwise tie, isolating received association influence. The sender has high
sociability; the recipient has zero sociability to isolate movement. These are
fixture settings, not changes to standard founding trait generation or rules.

For the illustrative seed 1:

| Observation | individual | social | sham |
| --- | --- | --- | --- |
| Sender hazard reward / learned value | -42 / -11 | -42 / -11 | -42 / -11 |
| Actual existing social contact | yes | yes | yes |
| Report / receiver value before moving | none / 0 | -6 / -2 | masked / 0 |
| Recipient destination | hazard (4,3) | safe (3,2) | hazard (4,3) |
| Recipient firsthand hazard episodes after tick | 1 | 0 | 1 |

The uninformed recipients learn after being hurt; the informed recipient moves
safely with a received episode and no physical hazard episode. `demo.json`
contains the full evidence trace; `results/demo-*.json` retain complete world
snapshots. The example is the first positive seed after reporting the entire
predeclared ensemble, not a success-only cohort.

All seeds 1–64 were tested under all three conditions, with no contact/success
filtering. Eighteen seeds produced an eligible social contact. In ten, received
information changed hazard entry to safe movement. In the other eight contact
seeds the uninformed recipient already chose safely. Across all 64, recipient
hazard entries were **29 individual, 19 social, 29 sham**. All 18 informed
recipients had zero firsthand hazard experiences. Sham and individual behavioral
states and RNG matched exactly in all 64 probes. There are no additional RNG
calls in the channel.

The arena deliberately offers a useful lesson and a viable alternative. Its
success establishes the implemented mechanism's causal capability under those
conditions; it is not an unbiased estimate of usefulness in ordinary worlds.

## Short population pilot

The predeclared pilot used seeds 1–8, 500 ticks per condition, with standard world
creation and exactly 60 slots. No arena/trait interventions were used. A 200-tick
sample estimated 37.84 s of simulation for the campaign; actual aggregate stepping
was 38.13 s, excluding creation, checkpoints, validation and analysis.

| Total across eight worlds | individual | social | sham |
| --- | ---: | ---: | ---: |
| Descendant births | 392 | 401 | 392 |
| Deaths | 7 | 5 | 7 |
| Hazard encounters | 1,771 | 1,666 | 1,771 |
| Eligible information opportunities | 1,112 | 1,243 | 1,112 |
| Delivered messages | 0 | 1,243 | 1,112 masked |
| Scheduled decisions | 230,575 | 230,693 | 230,575 |

Communication altered trajectories, which changed subsequent proximity/contact
opportunities. The treatment therefore does not have the same realized contact
count as its controls. Raw encounters also reflect differing populations and
exposure; these totals are not equal-opportunity hazard rates.

Paired social-minus-individual differences per seed, with descriptive 95%
percentile bootstrap intervals (10,000 resamples of eight paired seeds; analysis
RNG seed 404):

| Outcome | Mean difference | Interval |
| --- | ---: | ---: |
| Living population at tick 500 | +1.375 | [-0.125, 2.875] |
| Births | +1.125 | [-0.25, 2.625] |
| Deaths | -0.25 | [-0.875, 0.25] |
| Hazard encounters | -13.125 | [-24.625, -3.0] |

These eight short runs suggest fewer encounters, not established survival
improvement. There were only 7 versus 5 deaths, the population difference interval
includes zero, and the worlds are young, before age-related turnover. The small,
fixed seed ensemble and bootstrap approximation limit generalization. No
endurance campaign, significance-driven expansion, or selection of interesting
population seeds occurred. Individual seed rows are in `results/pilot.csv`.

## Scheduling, RNG and performance

Communication piggybacks on an existing social decision, which already occupies
one of the 60 slots. It does not execute another world tick, biological update,
random draw or out-of-scheduler movement. No extra recipient decision is granted.
If the receiver's scheduled turn follows the sender's, it can use the association
that tick; otherwise it uses it on its next eligible turn. This ordering is the
existing deterministic schedule, not a simultaneous-message model.

There is deliberately no additional modeled energy/time cost beyond the existing
social action. That is a limitation, not a claim that communication is free in a
richer model. Real execution cost is measured: the post-decision contact hooks
summed to 0.0446 s across 4,000 social-condition ticks (about 0.35% of stepping
wall time). This excludes timer overhead and provenance work inside ordinary
`remember` calls; it is not a comprehensive profiler.

The single 200-tick sample measured reference 330.2 ticks/s, experimental
individual 317.8, social 313.2, sham 320.3. The 24 pilot runs ranged about
301–338 ticks/s. Timing order, noise and changed behavior prevent treating those
differences as controlled speed improvements. No optimization was attempted.

Matched seeds give identical initial conditions and RNG states. Off/individual
matches the reference exactly; sham retains the same behavioral trajectories and
RNG. Sham intentionally adds message records and can evict older episodes, so
full event/memory equality is neither expected nor claimed. Episodes themselves
are not read by the current movement rule; learned values are. Pilot sham checks
compare every non-episodic agent field, learned values, provenance, cells, original
events, RNG and scheduler. Social movement changes candidate sets; even a call to
`choice` can then consume a different number of random bits. Later social
trajectories and draw consumption are not held identical. No common-noise
counterfactual or long-term causal survival estimate is claimed.

## Persistence, observatory and verification

The experimental subclass has a separate SQLite checkpoint table storing a full
checksummed state/config/provenance envelope in one atomic transaction. It uses
`save_experiment`/`load_experiment`, not the standard Phase 3 saver. Standard and
unrelated databases are rejected as output targets, and uninstrumented Worlds
are rejected before creating a file. Legacy archived checkpoints remain handled
by their unchanged loader. Do not pass experimental worlds to the standard
Pygame/headless persistence entry point; that format cannot retain this sidecar.
The prototype format favors inspectability over large-history checkpoint speed.

All 24 saved pilot states matched published digests, independent replay and ten
additional ticks of exact restored continuation. All eight individual conditions
matched freshly run reference worlds. All eight sham conditions matched the
corresponding individual behavioral/RNG state, excluding added message records
and episode retention as stated above. `verification.json` records these checks;
`checkpoint-manifest.json` records local generated file hashes. Experimental
snapshot ownership defects and corrections are documented in `DEFECTS.md`.

The observatory adds `l` for living descendants and `f` for original founders,
with identity-preserving selection across roster changes. It shows actual
provenance, `hear` episodes and recent communication events. To inspect the
completed pilot (frozen/read-only):

```bash
.venv/bin/python -m gnome_fortress.observatory --communication social --checkpoint research/phase4a/results/pilot-01-social.sqlite
```

Press `l`, select a descendant, and use PgUp/PgDn. Living descendant **87**, parents
50 and 41, had nine socially received hazard associations, no firsthand hazard
experience, and strength -18 at tick 500. Its last source was 63, itself a
firsthand-experienced descendant. This is a real pilot record, not an injected
persona. `unexposed-descendant-persona.txt` and `unexposed-descendant-screen.txt`
show the data. `descendants-terminal.ansi` captures a real terminal navigating to
87 and its provenance. The source checkpoint SHA-256 remained unchanged.
`python -m research.phase4a_capture` reproduces that terminal check after the pilot.

Initial focused tests: 10 passed, then 26 with the existing observatory suite.
After added persistence tests exposed ownership defects and corrections: 31
passed. Broader fast regression: **102 passed in 132.13 s**, including research
controls and unchanged reference equivalence. A final writer-type guard and its
new regression were followed by the final targeted suite: **32 passed in
6.52 s** (103 distinct fast tests exercised across the overlapping runs). The one prolonged unattended test and historical archive campaign
were excluded. No new package dependencies were added.

## Reproduction and next question

```bash
# Tiny causal demonstration (no files written):
.venv/bin/python -m research.phase4a_demo --seed 1

# Complete bounded pilot/probes in a NEW directory; existing output is refused:
.venv/bin/python -m research.phase4a_experiment --output run-results/phase4a-reproduction

# Independent replay/reference/control/continuation checks of that directory:
.venv/bin/python -m research.phase4a_verify run-results/phase4a-reproduction

# New live experimental world (paused; l selects descendants after births):
.venv/bin/python -m gnome_fortress.observatory --communication social --seed 1

# Fast relevant regression; no endurance campaign:
.venv/bin/python -m pytest -q tests research/test_analysis.py research/test_phase2.py research/test_study.py --ignore=tests/test_long_run.py
```

Deterministic state digests should match published CSV values. Wall-clock timings
will vary. SQLite files are generated local artifacts excluded from Git (about
25 MiB for this campaign); public CSV, evidence JSON, traces, manifests and source
are committed. The verification command writes its report beside the output
directory, so use a dedicated parent for a new reproduction if keeping its logs.

Before a separately approved endurance campaign, specify a survival estimand,
exposure-normalized hazard measures, seeds and duration, and decide whether this
fixed attenuation rule and absence of extra modeled communication cost are the
intended experiment. Mechanism capability is supported here; transmission fidelity,
misinformation, hearsay chains and information surviving generational turnover
remain untested. No civilization systems are implied or implemented.
