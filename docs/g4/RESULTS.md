# G4 engineering results

Accepted baseline: `40eeac5cb8893f02d32e456b4a778badf3cc998f`, inspected on
clean main. Added a presentation-only Advisor with four explicit conditional
topics, A/button, mouse/digit choices, Back/Close, truthful factual summaries and
navigation to existing statistics, events, Life, Direct Family and power records.
Selection and Watch persist through navigation. Escape retains save-and-exit.

## Executed verification

- Targeted Advisor/G3/G2/viewer tests: **34 passed in 10.63 seconds**.
- Relevant complete fast regression suite: **193 passed in 159.80 seconds**.
  Excluded only `tests/test_long_run.py`; no long research campaign was executed.
- Tests exercise every branch, invalid choice, Back/Close, current population,
  recent recorded deaths, missing/awake/sleeping/deceased selections, lifecycle,
  overlap, resource accounting, mouse navigation, small panels, Watch preservation,
  exact world/RNG state, cadence invariance, save/load, save/exit and extinction.
  Existing regressions cover Rain/Drought, Life/family, corruption rejection,
  shutdown, historical reference equivalence and persistence behavior.
- G1, G2 and G3 writer-generated active-effect snapshots loaded unchanged;
  old-reader roundtrip and **90-tick exact continuation** passed for each.
- Actual **X11 Pygame 1334 × 820** operational check used scripted queued key/mouse
  events. Captured five actual screens: main, world, gnome, powers and complaint.
  Natural seed-1 founder 53 remained watched after its recorded hazard death.
  Ledger navigation, read-only drawing, save/load and Escape passed.
- Visually inspected main-menu and intervention screenshots. No human usability
  session was conducted. No claim of enjoyment follows from automated checks.
- `compileall` and `git diff --check` passed.

## Preservation and limits

The verification audited **523 pre-existing tracked files** against G3, excluding
only the intended root README and God viewer changes. Historical CSV checkout
line-ending normalization was accepted without rewriting original records.
**Ten authoritative/presentation modules** remain byte-identical: engine, model,
game, game_storage, storage, runtime, god_demo, viewer, game_presentation and
life_presentation. Research datasets, prior evidence, historical tags and the
mode contract remain preserved. No save-format change or migration occurred.

No confirmed core defect was found or corrected. The dialogue adds no simulation
state, RNG draws, events, mechanics, dependencies or NPC memory. Current overlap
and cumulative overridden-cell pulses are explicitly separate. Resource deltas
are not reported as survival benefits or causal death explanations.

Facts are snapshots sampled on choice; select again to refresh during play.
The overlay temporarily covers existing side-panel inspection. Recent-death
queries can examine many existing indexed events on demand when deaths are rare;
they do not rescan history per frame or create permanent new indexes. Existing
full-snapshot and growing-history costs remain. No long-run capacity or Ironman
recovery guarantee is added. No G5 work began.

[Launch/controls and screenshots](README.md) · [Targeted tests](targeted-tests.txt) ·
[Fast tests](fast-tests.txt) · [Compatibility/audit/captures](evidence/verification.json).
The final full commit SHA is supplied in delivery and discoverable with
`git log -1 --format=%H -- docs/g4/RESULTS.md`.
