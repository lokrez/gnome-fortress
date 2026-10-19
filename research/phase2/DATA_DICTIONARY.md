# Phase 2 data and reproducibility

Core source, the original 27 tests and all Phase 1 historical files remain unchanged.
The default remains 60 slots. Phase 0 is f32c1a6, phase0-verified; Phase 1 is 232dd30,
phase1-verified. The experiment controls/runners are frozen in commit 1e67c3e.
The scaling manifest records the checkout parent at launch plus exact source hashes;
those files were subsequently committed without changing their experimental logic.

## Conditions and checkpoint safety

`Config(slots, memory)` is external experiment metadata. `capacity()` temporarily
sets the BASELINE engine module constant in a fresh process, and restores it on
exit. No file/default is edited. World ordering and all decisions remain original.
Never run different capacities in threads in the same process. Parallelism is
across independent world processes, never inside one world's decision order.

For ablation, only the learned `move:*` score readout is masked. The original
`remember` function temporarily sees the REAL previous association and records
normal consequences; records, visits and traits remain intact. A complete actual
learned table is saved even for an ablated world. Ablation is reapplied by its
experimental class after reload. Ordinary CLI loading is not a treatment loader.

Experimental SQLite files have sibling `.config.json` files. Use `load_experiment`
inside the matching capacity context, with an expected configuration. Non-60
checkpoints cannot be loaded safely by the normal 60-slot CLI. A missing/mismatched
configuration is an error. Standard application checkpoints remain unchanged.

## Run structure

Raw output: `data/{memory,scaling,endurance}/RUN/` (ignored by Git; retained locally).
`spec.json` fixes inputs; `summary.json` has logical results/digests;
`performance.json` separates simulation-loop timings from replay and export costs.
Each folder has `agents.csv`, `population.csv`, `final.sqlite` and its configuration.
Midpoint endurance snapshots and their continuation-check records are retained.
The compact archive intentionally omits large SQLite files, which can be regenerated.

The runner refuses an existing output folder. To reproduce one run, copy a published
spec, change ONLY `out` to a fresh directory, and execute:

```bash
.venv/bin/python -m research.phase2_run --spec copied-spec.json
```

Reproduce full campaigns from a checkout with empty Phase 2 raw output directories:

```bash
.venv/bin/python -m research.phase2_benchmark
.venv/bin/python -m research.phase2_campaign --workers 6
.venv/bin/python -m research.phase2_tailbench
.venv/bin/python -m research.phase2_analyze
.venv/bin/python -m research.phase2_extinction
.venv/bin/python -m research.phase2_lifespans
.venv/bin/python -m research.phase2_verify
.venv/bin/python -m pytest tests research -q -s
```

The endurance specs use original Phase 1 seed-1/2/3 tick-20,000 SQLite snapshots.
If those local files are absent, regenerate them using the Phase 1 runner and
verify the archived Phase 1 final logical digests before extension. On a fresh
checkout where `research/phase1/data` does not exist, the exact prefix command is:

```bash
.venv/bin/python -m research.study --seeds 1 2 3 --ticks 20000 --sample 100 --workers 3
```

Compare the resulting summaries' `final_digest` values with the preserved
`research/phase1/results/seed_summary.csv` for seeds 1–3 before running C. Do not
run this over existing historical data; use a fresh checkout for regeneration.
This reuses a
verified prefix, not a fresh world with the same living count. Scientific output
values/digests reproduce on the recorded Python/rule version; wall-clock timings,
RSS and physical SQLite-file bytes need not. Existing research requirements apply.

## Population samples and lifetime records

Sample interval: 100 ticks, including an initial row. Time is integer world ticks.
`births_total` includes 60 founders, while positive-interval births are offspring.
`agent_ticks` sums LIVING agents at the beginning of each tick before biology;
newborns enter biology the following tick. `decisions`, `eligible_agent_ticks`,
`capacity_slot_ticks`, `retained_slot_ticks` are interval counts. Scheduler eligibility
is after biology but before decisions; retained slots are after sleep/death clears.
`eligible_at_schedule` is a single final-tick count, blank in the initial row.
`decisions/agent_ticks` counts actual opportunities per living biological exposure,
including sleepers. `1-decisions/eligible_agent_ticks` is waiting among opportunities,
not permanent exclusion of a fixed fraction of agents.

Food stock is actual resource units across the map. `forage_cells` have >=10 food.
`food_consumed` is actual portions removed, which can exceed needs satisfied because
hunger floors at zero. Hunger/thirst over 100 and mean needs are end-of-sample living
states, not continuous-time averages or proof of global resource exhaustion.

Generation is founders=0 and child=1+max(parent generations). Maximum generation
includes deceased identities. Mean alive generation is current living agents only.
Lifetime age equals founder initial age plus time since entry; offspring initial
age is zero. Died=0 records are right-censored at the horizon. Complete-cohort
lifespan includes ALL offspring born by horizon-3,000, without a survivor or
minimum-decision filter. Slots do not alter maximum biological lifespan.

Own action counts in `agents.csv` cover the MEASURED run segment. For resumed C runs,
these cover ticks 20,001–100,000, while ages, children, ancestry and death labels
cover entire lives. C `extension_counters` measure only that extension; `events`,
`death_causes`, total births/deaths and lifetime distributions use the whole archive.
The Phase 1 prefix provides earlier population and slot measurements. No zero
food/pressure observations are invented for the unmeasured prefix.

## Performance and uncertainty

B uses sequential fresh processes. Loop wall/CPU timing includes sidecar counters
and sampling, excludes construction, digesting, validation, SQLite output and replay.
Full enabled replays use the ORIGINAL uninstrumented World with the same module
capacity, so their separate wall time also indicates instrumentation overhead.
CPU% = 100 * process CPU seconds / loop wall seconds: 100% means ONE logical CPU,
not the entire 16-thread machine. The 16-logical-CPU fraction is also recorded.
`simulation_peak_rss_mib` is process high-water RSS measured BEFORE final export and
replay; `overall_peak_rss_mib` additionally captures those costs. On C, the former
can include initial checkpoint loading and a midpoint fork check; do not treat it
as a clean isolated performance benchmark. GPU/VRAM are unused.

Scheduler seconds measure ONLY the call to original `World.schedule`, not decision
execution or biology. Synthetic cases hold populations, sleepers and deaths fixed
and make 10,000 selection calls without biological time; their five block timings
are variability observations, not independent scientific replicas.

Memory contrasts are enabled minus ablated, at the world-seed level (20 pairs).
Bootstrap percentile 95% intervals resample PAIRED seed differences 10,000 times
with NumPy seed 20261019. Paired-t intervals are a sensitivity check. Absolute
contrasts have endpoint-specific units; relative mean changes compare condition
means. Secondary endpoints are exploratory and not familywise-adjusted. Matching
initial seeds does not preserve common future random shocks after policies diverge.

## Supplements and integrity

Extinction intervals and late-window timings were declared in separate addenda
without changing the registered primary analysis. The tail benchmark uses 200
original-engine ticks per case, fresh quiet processes, and excludes loading. Its
RSS includes checkpoint loading. Only seed 1 at tick 100,000 has a production
save-time probe; other rows contain empty optional fields. That save occurs at
tick 100,200 in a separate file, not in the scientific archive.

After analysis and independent verification, build and verify the compact bundle:

```bash
.venv/bin/python -m research.phase2_package
sha256sum -c research/phase2/SHA256SUMS.txt
sha256sum -c research/phase2/CONTENTS.sha256
```

`checkpoint-sha256.txt` records local SQLite bytes, not portable logical-state
expectations. `results/archive-checks.csv` and each run's summary record logical
digests. Full replays cover the first matched pair for 20,000 ticks and seed 11
at every capacity for 3,000 ticks. Endurance checks compare checkpoint state and
32-tick continuations at ticks 50,000 and 100,000; they are not full duplicated
100,000-tick runs. All 58 final archives are reconciled independently against
events, ancestry, individual records and sampled population/exposure counts.

The packaging command includes archival guards for ALL ten original Phase 1 SQLite
files and its published bundle. Those byte checks require the preserved local
artifacts; portable scientific regeneration instead verifies logical digests. It
is not necessary to rebuild the publication bundle to reproduce an individual
trajectory or the paired analysis. To inspect the delivered compact archive
without overwriting this checkout:

```bash
python3 -m zipfile -e research/phase2/phase2-study.zip /tmp/gnome-phase2-study
cd /tmp/gnome-phase2-study
sha256sum -c research/phase2/CONTENTS.sha256
```

`results/lifespan-distributions.csv` summarizes the registered secondary lifetime
outcomes. It keeps founders versus offspring and completed deaths versus living
right-censored records separate in every run. Quantiles are descriptive NumPy
linear quantiles, not independent-agent uncertainty intervals. Current ages of
survivors are not completed lifespans. Founder biological age includes initial
age; observed time since entry is reported separately. These summaries contain
all agents, without the Phase 1 minimum-decision survivor filter.
