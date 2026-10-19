# Phase 1 data and reproduction

Run from repository root using the tested Python environment:

```bash
.venv/bin/python -m research.study --workers 4 --out new-empty-study-directory
.venv/bin/python -m research.analyze --data new-empty-study-directory --out new-results-directory
.venv/bin/python -m pytest -q -s
.venv/bin/python -m pytest research/test_study.py -q
```

Study defaults are the pre-registered ten seeds and 20,000 ticks. Use an empty output
location: the runner refuses to overwrite any seed directory. Four independent
processes shorten elapsed time without affecting each world's ordering. No engine
source files are modified; the runner refuses mismatches against f32c1a6. The
runtime is Python 3.14.4; analysis-library versions are in `research/requirements-tested.txt`.
This environment includes extra scientific libraries beyond the original engine.
The raw CSVs are flat numerical research telemetry emitted by the measurement
script, not a workbook requiring recalculation. Empty values mean not applicable;
zero means measured zero. Time is always integer world ticks, not seconds.

## Per-seed raw files

`population.csv`: one row at tick 0, then each 100 ticks through tick 20,000.
`living` is the end-of-tick stock. `births_total` includes 60 founders; all positive-
tick `births_interval` count offspring. `deaths_total` and `deaths_interval` are
permanent losses. Identity: seed, tick. Each interval covers ticks after the previous
row through the current row, inclusive of the current tick. Tick-zero intervals
are zero. `eligible_agent_ticks` counts awake, living eligibility opportunities at
the scheduler AFTER biology but BEFORE decisions/births. `decisions` counts own
assignments executed (including a fatal move). `retained_slot_ticks` counts occupied
slots AFTER deaths/sleep relinquishment. `capacity_slot_ticks` is 60 times interval
length. `sleeping` is open sleep spells at the row boundary. `hazards` and `social`
are interval encounter and initiated-interaction counts.

`agents.csv`: one row per identity ever born. Identity: seed, agent. `founder` and
`died` are 0/1. Blank parent1/parent2 marks founders; blank death_cause means still
alive. `born_tick` is entry; founders have separate `initial_age`. `end_tick` is death
or horizon. `age_ticks = initial_age + observed_ticks`; for offspring, observed
exposure is end_tick-born_tick. A death tick includes that tick's biological update.
Living records are right-censored at horizon. `children` includes both parental
roles, so the sum is twice offspring count. Traits are inherited 0–100 integers.
Action columns count OWN decisions; receiving social/reproductive effects does not
count as an own decision. `move` includes fatal movement. `novel_moves` counts first
entries into a cell (the initial spawning cell is not recorded until entered).
`unique_visited_cells` reconciles to novel_moves. `hazard_entries` is a subset of
moves. Resource/eating/drinking quantities are not inferred from action counts.

`sleep.csv`: one row per sleep spell, keyed by seed, agent, start_tick. `planned_end_tick`
is the rule's original deadline. `end_tick-start_tick = duration_ticks`. `status`
is wake, death, or censored at horizon. Death-interrupted and censored spells are
not completed sleep-duration observations. Sleep-start ticks at the horizon can
produce zero observed duration. Planned 12-tick sleep reduces fatigue on 11 later
biological updates because wake eligibility is exclusive of sleep_until; elapsed
spell length remains 12. This is the preserved baseline convention.

`summary.json`: final counters, state digests, recorded death causes and sleep status
counts. `execution.json` records elapsed seconds and is expected to vary between
runs. `manifest.json` records seeds, horizon, baseline commit, runtime, protocol/
harness hashes, and an initial observer-neutrality replay check. State digests, CSVs
and scientific summaries should reproduce; execution timing is not a state variable.

`final.sqlite` is retained locally in each raw directory. It is intentionally excluded
from the compact CSV archive. Checkpoint hashes are listed separately; a new SQLite
file can have different physical bytes while the logical state digest is identical.

## Derived results

`seed_summary.csv`: exact final counts, tail (tick >=10,000) mean/range, least-squares
population slope in gnomes per 1,000 ticks, detrended population SD/mean, last and
preceding 5,000-tick mean ratio, total decision/retained utilization and waiting
fraction. Rates use summed numerators and denominators. Tail statistics use sampled
100-tick endpoints (101 points including tick 10,000); adjacent 5,000-tick means each
use 50 endpoints excluding the left boundary. `sampled_peak_population` and tail
min/max in this table use the sampled endpoints. `exact_population_checks.csv`
reconstructs end-of-tick population at EVERY tick from all birth/death events and
reports exact peaks, tail extrema and extinction checks.

`lifespans.csv`: age quantiles separately for completed founder deaths, completed
newborn deaths and right-censored newborns. Min/q10/median/q90/max are ticks. Do not
interpret the median age of censored agents as a median completed lifespan.
`offspring_survival.csv` contains per-seed Kaplan–Meier estimates with tied deaths
before administrative censoring at the same age. Birth cohorts experienced different
ecology; curves are descriptive, with no claim of independent identical lifetimes.

`sleep_durations.csv`: status-specific duration quantiles, per seed.
`trait_correlations.csv`: within-seed Spearman coefficients for early-born offspring
(born <=17,000, >=100 own decisions). All selected lifetimes are complete because
maximum rule lifespan is 3,000 ticks. The decision threshold excludes early deaths,
so behavioral associations remain subject to survivor/selection bias and ancestry,
cohort, spatial and genetic confounding. No agent-level significance tests are used.
`trait_correlation_summary.csv` gives median/min/max correlations and positive signs
across the ten seeds; these are descriptive ranges, not confidence intervals.

`autocorrelation.csv`: later population after linear detrending, sampled every 100
 ticks, raw autocovariance normalized by lag-zero energy. The spectrum is restricted
to periods 300–5,000 ticks and normalized within that band. Temporal autocorrelation,
short samples and multiple peaks prevent a simple periodicity claim.
`findings.json` collects pooled distributions and seed-level ranges for the report.

PNG figures are accompanied by editable SVG versions. The zipped raw data preserve
all CSVs, JSON manifests and logs. SHA256SUMS.txt verifies CSV/archive/plot files;
the ten local checkpoint-file hashes are in checkpoint-sha256.txt. The Git tag
phase0-verified always points to the original verified commit.

## Compact archive

`population-study.zip` contains the raw CSVs/JSON, plots, report, protocol, research
code and test logs (about 7 MB), retaining their repository-relative paths. The ten
large SQLite checkpoints remain available locally but are excluded from the bundle.
To inspect a standalone extraction without overwriting this checkout:

```bash
python3 -m zipfile -e research/phase1/population-study.zip /tmp/gnome-population-study
cd /tmp/gnome-population-study
sha256sum -c research/phase1/CONTENTS.sha256
```

The checksums include the archived raw records as well as the figures and code.
