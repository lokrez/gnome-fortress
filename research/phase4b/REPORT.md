# Phase 4B — the telephone experiment

**Finding:** the controlled A → B → C chain can change C's movement before
firsthand hazard exposure. This meets the narrow mechanism criterion, not a claim
of spontaneous dialogue, culture, or improved population survival.

References: Phase 3 `2f5213c23300e61330ea665bfb4789622bf38bc6`; Phase 4A `e8eac96`.
All nine pre-existing application files are unchanged. Earlier tags and datasets
are preserved. New `TelephoneWorld`/config and a research-only harness are separate.
The standard simulator and Phase 4A keep their original behavior. Phase 4A's
10/64 two-agent result and short pilot remain as reported, with survival benefit
unproven. Do not compare its effect fraction directly with this different fixture.

## What inspection established

Phase 4A rejects senders without firsthand experience, so it cannot already
perform this chain. Its last-source/counter fields do not preserve multihop paths,
and repeated messages can reinforce the same association. `move:hazard` means a
movement score associated with a **terrain class**, not a location, sentence,
probability or calibrated confidence. The single topic remains fixed. There is
no stochastic content mutation, invented language, or global information source.

## Protocol and controls

Seeds 1–64, five conditions, three ticks per trial; no success filtering. Exactly
60 founder identities and scheduling slots remain; 57 founders are permanently
killed with `experiment_setup` for the fixture, leaving A=1, B=2, C=3 alive.

A actually enters hazard (5,3) through the original movement/consequence code at
tick zero. A meets B at (4,3) during a prescribed contact action in tick 1. B then
moves normally to (3,3). C sleeps until tick 2 at (2,3). B contacts C in tick 2;
C's movement follows in tick 3. C cannot receive directly from A (distance 3).
The scheduler, biology, movement scoring and RNG implementation are unchanged.

Meetings/waits are **scripted scheduled interventions**, not autonomous choices.
There are eight scheduled actions and two physically valid contact opportunities
per trial under every condition. C precedes B in the tick-2 waterfall ordering,
so C waits rather than resetting the scheduler to force an earlier lesson.

B has caution 100 and hunger 50 to ensure the same safe transit without peer
attraction or firsthand hazard exposure. C has zero curiosity/caution/sociability;
its two safe grass neighbors and one hazardous neighbor otherwise tie. Needs,
cooldowns, map and other fixture settings match across conditions. Source
preconditioning is an explicit unscheduled intervention, not an extra free
message/action during normal simulation.

| Condition (64 trials each) | Delivered packets | Correct two-hop warnings at C | C hazard entries |
| --- | ---: | ---: | ---: |
| Individual: communication off | 0 | 0 | 20 |
| Direct: A→B, forwarding disabled | 64 | 0 | 20 |
| Multihop: A→B→C | 128 | 64 | 0 |
| Masked: same two-hop opportunities, opaque receipts | 128 | 0 | 20 |
| Irrelevant: forwarded weight applied to grass | 128 | 0 | 64 |

All conditions had 128 contact opportunities and 512 scheduled actions across
the cohort. All C agents had zero firsthand hazard exposure before the decision.
The multihop condition prevented hazard entry in **20/64 matched trials**; in the
other 44 the uninformed C already chose safely. All 64 multihop trials delivered
a source-verified warning through B, which itself had no firsthand hazard exposure.

The irrelevant control changes only the forwarded association key to `move:grass`
in the harness, retaining the weight and contacts. C then avoids grass and enters
the hazard. The production config rejects this control; it is not a general
misinformation mechanic. Receipt records explicitly identify the intervention and
preserve the original hazard grounding. This demonstrates content-sensitive
behavior, not a generic benefit from communication occurring. Internal
`meaningful_messages` counts unmasked association updates, including the wrong
key in this control; it does **not** mean verified useful information.

## Causality, fidelity and limits

All five conditions have identical RNG state immediately before C's movement.
Individual and masked core states match after excluding `hear` episodes. Direct
retains real knowledge at B, so complete agent-state equality with individual is
not expected; C's corresponding state/RNG match. A separate seed-1 readout
ablation holds B and the received chain fixed and sets only C's hazard score
weight to zero: C switches back from safe movement to hazard entry.

The old half/quarter arithmetic is retained exactly:

```
packet = sender_weight // 2
recipient_weight = clamp((3*old_weight + packet) // 4, -100, 100)
```

Seed 1: A's real damage reward is -42, its learned weight -11; A sends -6, B
acquires -2; B sends -1, C acquires -1. Topic, source path and deterministic
arithmetic are preserved, but **numeric strength is not transmitted verbatim**.
Across this cohort C's final warning is always -1. Integer floor division keeps
-1 negative through additional allowed hops; this persistence is a rounding
property, not evidence of reliable confidence or preserved detail. No telephone
jitter was added to produce it.

The useful effect is a tie-break in an engineered setting. A targeted sensitivity
test gives the two grass tiles the existing -8 revisit penalty: the same -1
warning then fails and C enters the hazard. Neither all preferences nor resource
pressure can be assumed overcome. No population campaign, mortality/survival
benefit, transmission-prevalence estimate or natural chain frequency is claimed.
After C's choice, differing candidate sets/encounters can change RNG consumption;
exact later trajectory matching between content treatments is not expected.

## Bounded provenance and safety

Each retained identity/topic has one current proof: physical root ID/tick/
experience counter/reward, participant IDs, and at most seven structured receipts
(eight participants maximum). Receipts include source/recipient coordinates,
timestamps, weights and firsthand status at acquisition. A first physical hazard
can ground a fresh root; if its EMA retains prior social influence the root is
marked `prior_social`. This is not a count of statistically independent evidence.

There is one social acquisition per topic: duplicates, alternative-root
reinforcement, loops and forwarding beyond the cap are rejected. This deliberately
conservative policy differs from Phase 4A's repeated assimilation; Phase 4A itself
is untouched. Latest physical grounding may replace a current proof, so each
agent's latest movement also retains its bounded pre-decision proof input. That
keeps the actual acquisition and outcome distinguishable in controls where C
subsequently learns firsthand.

Only the last 128 telephone audit entries are retained; new trivial telephone
interactions are not appended to core event history. Self-contained proof paths
remain inspectable after audit eviction. Existing core event/identity history
remains unchanged. Storage is bounded **per retained identity/topic plus the
fixed audit ring**, not constant for an indefinitely growing population.

After 500 warm-up duplicate attempts plus 10,000 more, all physically local and
rejected as `duplicate_root`, the audit remained 128,
C's proof retained two receipts and weight -1, message count stayed 2, and no core
events were added. Retained traced allocation grew 32 bytes (counter bookkeeping),
not per-message records. See `bounded-storage.json`.

Missing/nonlocal/asleep/dead current senders cannot deliver; dead historical roots
can remain legitimate evidence. Tests cover duplicate/loop rejection, interrupted
relays, hop limits, source/spatial forgery, checksum corruption, snapshot ownership,
read-only inspection, mid-chain reload and transactional write failure.
`DEFECTS.md` records corrected test assumptions and evidence-retention findings.

## Execution cost and verification

Small isolated-process measurements used 64 trials per condition, each with the
same 192 ticks/512 scheduled actions. `tracemalloc` was enabled:

| Condition | Stepping wall ms | Peak traced allocation bytes | Peak RSS KiB | Max added state bytes |
| --- | ---: | ---: | ---: | ---: |
| Individual | 21.93 | 348,458 | 24,360 | 2,020 |
| Direct | 29.63 | 352,969 | 24,632 | 3,197 |
| Multihop | 38.58 | 356,762 | 24,728 | 4,506 |
| Masked | 40.47 | 356,490 | 24,432 | 4,292 |
| Irrelevant | 45.61 | 357,647 | 24,144 | 4,742 |

In this instrumented sample multihop adds about 0.260 ms per three-tick trial and
8.1 KiB peak traced allocation versus the instrumented individual condition.
These very short samples include different C outcomes, trace allocation overhead
and concurrent regression activity. They are not mature-world throughput or
precise production overhead estimates. Stepping excludes setup/validation/JSON;
allocation peak includes construction, and RSS also includes imports/serialization.
No extra scheduler slot is consumed beyond the prescribed contact action. Normal
TelephoneWorld operation uses the existing social-decision slot, with no new RNG
draw or separate recipient decision.

All **320 trial replays** matched every CSV measurement and full digest, and all
five saved examples matched their independent replay. The focused suite passed
31 tests after documented assertion corrections; the larger targeted suite passed
52. Broader fast regression: **123 passed in 133.05 s**. Final targeted tests,
including the C-only readout ablation: **53 passed in 8.29 s**. This exercises 124
distinct fast tests across overlapping runs. The prolonged unattended test and
historical archive campaign were deliberately excluded. Source hashes and exact
reference commits are in `environment-and-integrity.json`; no dependencies added.

## Run and inspect

```bash
cd ~/gnome-fortress
.venv/bin/python -m research.phase4b_demo --seed 1
# Optionally save to a NEW path (create its parent directory first):
.venv/bin/python -m research.phase4b_demo --checkpoint run-results/telephone.sqlite
.venv/bin/python -m research.phase4b_inspect run-results/telephone.sqlite --agent 3
```

The companion is read-only and shows C's root A, immediate source B, complete
receipt path, firsthand status at acquisition, actual score inputs and movement.
`c-inspection.json` is its real output for the saved multihop example. The existing
Observatory is unchanged. Checkpoints use a separate checksummed, atomic SQLite
format with explicit harness loading; other database formats are refused as output.
The demo refuses existing output paths. Generated SQLite files are local artifacts
excluded from Git, with hashes in `verification.json`.

Reproduce the entire small cohort in a **new directory**, then verify it:

```bash
.venv/bin/python -m research.phase4b_experiment --output run-results/phase4b-reproduction
.venv/bin/python -m research.phase4b_verify run-results/phase4b-reproduction
.venv/bin/python -m research.phase4b_benchmark --condition multihop
.venv/bin/python -m research.phase4b_benchmark --stress
```

CSV digests should match; timings need not. Verification writes a report beside
the output directory, so give reproductions a dedicated parent for separate logs.
A sensible next experiment is a predeclared comparison of warning strength against
competing movement scores, before inferring natural propagation or survival value.
No rounding change, new distortion model or endurance campaign is introduced here.
