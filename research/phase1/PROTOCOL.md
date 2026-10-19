# Phase 1 protocol (fixed before the study runs)

Baseline: f32c1a6, tagged phase0-verified. Do not edit gnome_fortress/ or its tests.
Ten seeds: 1,2,3,4,5,6,7,8,9,10. Horizon: 20,000 integer ticks per seed.
60 founders, standard 48x32 map and all default rules. No interventions.
Run independent processes; process order has no meaning. Sample population and
interval counts every 100 ticks, and retain each lifetime and each sleep episode.
Count every own decision using an external subclass that delegates to the original
rule methods and does not touch RNG, agents or cells. Check observer neutrality
against the uninstrumented baseline before launching the full study.

Outputs: per-seed population CSV, per-agent CSV, per-sleep-episode CSV, per-seed
summary JSON, final SQLite state, and initial/final digests. Record file hashes.
Final SQLite archives are reproducibility aids, not required to analyze the CSVs.

Population: exact end-of-tick living stock. Birth totals include 60 founders;
interval birth counts at tick>0 are offspring. Deaths are recorded causes of the
terminal rule, not a causal decomposition of preceding damage. Lifespan: completed
biological age and time since entry are separate. Founders have pre-existing ages;
exclude founders from the newborn survival curve. Living identities at horizon
are right-censored. Sleep durations: wake, death-interrupted and horizon-censored
spells are separate, measured as end tick minus sleep-start tick.

Scheduling: assigned decisions/60 ticks, retained end-of-tick slots/60 ticks,
and eligible awake agents at scheduling are distinct. Aggregate ratios from counts,
not averages of per-agent ratios. Retained slots underestimate executed decisions
when agents sleep or die. Waiting fraction = (eligible-assigned)/eligible.

Traits: report within-seed Spearman associations between each inherited trait and
per-decision hazard entries, social initiations, new-cell movement fraction,
parenthood rate and lifespan, using post-founder agents born by tick 17,000 for
behavioral analyses, with at least 100 own decisions. Lifetime association uses
completed deaths only, explicitly subject to survivor bias. No causal interpretation,
no independent-agent p-values: ancestry and shared environment induce dependence.
Report distribution of ten within-seed correlations, not only a pooled estimate.
The 17,000 cutoff and 100-decision threshold are fixed before results.

Population characterization: examine the final 10,000 ticks, linear trend per
1,000 ticks, final/preceding 5,000-tick means, detrended coefficient of variation,
and autocorrelation/periodogram after detrending. A finite run cannot prove a stable
stationary distribution or rule out eventual extinction or long-term growth.
Any observed recurring spectral peak is descriptive; no significance claim or
classification as a periodic oscillator without further independent validation.

Memory experiments: specify separate, controlled mechanism and whole-world
ablations in MEMORY_EXPERIMENTS.md. The ten observational runs remain enabled.
No selection of seeds or horizons after looking at outcomes. Report defects before
fixes; simulation-rule fixes are outside this observational phase.
