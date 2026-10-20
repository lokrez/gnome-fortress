# Gnome Fortress — project-lead review handoff

Prepared 2026-10-20. Repository: **[lokrez/gnome-fortress](https://github.com/lokrez/gnome-fortress)**.
The repository is private: the reviewing chat needs authorized repository access,
or the relevant files supplied directly. A URL alone does not grant access.

Review the implementation and evidence at **[Phase 4B commit 2644229](https://github.com/lokrez/gnome-fortress/commit/2644229a5665a2a8fb6bf60f499fe841b075a29e)**.
This handoff adds documentation, not new simulation behavior or experiment results.

## What is established

Gnome Fortress is a deterministic Python/SQLite/Pygame artificial-life experiment,
with 60 founding identities and 60 decision slots by default. The terminal
observatory adds inspection without changing the standard simulation.

Phase 4A demonstrated a narrow, local transfer of an existing hazard association:
10 of 64 matched two-agent seeds changed hazard avoidance after receipt. Its
short eight-seed pilot recorded 1,666 hazard encounters with communication versus
1,771 without. Survival improvement remains unproven.

Phase 4B asks whether A can inform B, and B then inform C without B or C first
experiencing the hazard. Its **controlled mechanism test succeeded**: all 64
multihop trials delivered a grounded A→B→C warning, and 20 changed C from hazard
entry to safe movement before firsthand exposure. This is a different fixture
from Phase 4A; the two effect fractions are not comparable performance estimates.

## Phase 4B controls

All 64 seeds were tested under all five conditions, without success filtering.
Each trial used three ticks, eight scheduled actions and two local contact
opportunities. The fixture preserves 60 founder records but kills 57 with an
explicit setup cause, leaving three living participants.

| Condition | Packets delivered across 64 trials | Correct two-hop warnings at C | C hazard entries |
| --- | ---: | ---: | ---: |
| Individual learning | 0 | 0 | 20 |
| Direct transfer only | 64 | 0 | 20 |
| Multihop transfer | 128 | 64 | 0 |
| Masked-information control | 128 | 0 | 20 |
| Irrelevant-information control | 128 | 0 | 64 |

The irrelevant control applies the forwarded weight to grass instead of hazard
terrain, only inside the harness. C then avoids grass and enters the hazard.
Masked packets preserve the delivery opportunity without updating score weights.
All conditions had identical RNG state immediately before C's decision. Exact
later matching is not assumed after movement/candidate sets diverge. Individual
and masked core states match after removing received-message episodes; the direct
condition legitimately retains different knowledge at B.

A separate readout ablation holds B and the chain fixed, removes only C's hazard
score weight, and restores hazard entry in seed 1. Receiving a packet alone is
therefore not the reported success criterion: actual movement was measured.

## Important limitations

- Meetings and waits are prescribed scheduled interventions. Spontaneous dialogue
  or naturally sustained multihop propagation has not been established.
- C's otherwise tied movement choices make the fixture deliberately sensitive.
  Original attenuation reduces seed-1 weights from A=-11 to B=-2 to C=-1. That
  final one-point penalty breaks the tie; an existing stronger preference defeats
  it in a sensitivity test.
- Floor division preserves a minimal negative weight through additional allowed
  hops. This is arithmetic behavior, not calibrated confidence or numeric fidelity.
- Association keys describe terrain classes, not locations or language. No culture,
  general intelligence, long-term survival benefit or civilization is claimed.
- Provenance is bounded per retained identity/topic: maximum eight participants,
  seven receipts, a 128-entry audit ring and one latest movement input record per
  agent. An indefinitely growing population/core history is not constant-memory.
- Repeated/looping messages cannot reinforce the same topic. This conservative
  policy differs from Phase 4A; its original implementation remains unchanged.
- Instrumented three-agent trials measured about 0.26 ms additional time and
  8.1 KiB additional peak traced allocation for multihop versus individual mode.
  These short measurements do not characterize mature-world performance.

## Verification and preservation

- All **320 independent trial replays** and five saved examples matched exactly.
- **123 fast regression tests passed**; the final focused suite passed **53**.
  These runs overlap (124 distinct fast tests exercised), not 176 separate tests.
- Tests cover causal readout, loops, duplicates, missing/dead/nonlocal sources,
  interrupted relays, hop limits, mid-chain reload, transactional write failure,
  proof/checksum corruption, ownership and read-only inspection.
- Another 10,000 physically local duplicate attempts after warm-up left C's score
  and proof unchanged, retained 128 audit entries, and added no core events.
- All nine existing Phase 3/4A application files remain byte-identical to the
  Phase 4A reference. The four Phase 0–3 verified tags were pushed to GitHub.
- No endurance campaign or historical archive verification was rerun.

GitHub contains committed source, history, tags, reports, CSV data and evidence
JSON. Generated SQLite checkpoints are Git-ignored and remain local; this push
is not a backup of every research checkpoint. The small trials can regenerate
those files. A fresh checkout needs its Python environment installed before the
commands below; `.venv` itself is not committed.

## Review entry points

All links below are pinned to the reviewed code revision:

- [Full Phase 4B report and reproduction](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b/REPORT.md)
- [Telephone implementation](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/gnome_fortress/telephone.py)
- [Controlled harness](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b_experiment.py)
- [Per-seed CSV](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b/results/probes.csv)
- [C's recorded provenance and movement](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b/c-inspection.json)
- [Focused tests](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/tests/test_telephone.py)
- [Verification logs](https://github.com/lokrez/gnome-fortress/tree/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b/validation)
- [Source/reference integrity record](https://github.com/lokrez/gnome-fortress/blob/2644229a5665a2a8fb6bf60f499fe841b075a29e/research/phase4b/environment-and-integrity.json)

From an existing configured checkout:

```bash
.venv/bin/python -m research.phase4b_demo --seed 1
mkdir -p run-results
.venv/bin/python -m research.phase4b_demo --checkpoint run-results/review-telephone.sqlite
.venv/bin/python -m research.phase4b_inspect run-results/review-telephone.sqlite --agent 3
```

Use a new checkpoint path: the demo refuses to overwrite one. The companion
inspector is read-only and shows the source path, firsthand status at acquisition,
actual association inputs and resulting movement.

## Questions for the project lead

Please independently review whether the evidence supports only the narrow
mechanism claim or something weaker. In particular:

1. Do the controls and C-only ablation adequately isolate received content?
2. How much does the tie-sensitive fixture and negative floor-division behavior
   limit the result's relevance outside this arena?
3. Are the bounded proofs sufficient to distinguish transmission from independent
   experience without treating mixed-origin estimates as independent witnesses?
4. What should be measured next before authorizing longer population experiments?

My recommendation is a predeclared warning-strength versus competing-preference
experiment before claims about natural propagation or survival. No next phase or
long campaign has been started by this handoff.
