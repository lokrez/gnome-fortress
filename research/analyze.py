"""Recompute figures and summaries from immutable phase-1 telemetry."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from research.study import TRAITS, write_csv

COLORS = plt.get_cmap("tab10").colors
CAUSES = ("old_age", "starvation", "dehydration", "hazard")
METRICS = ("hazards_per_100_moves", "social_per_100_decisions", "novel_move_fraction", "parenthood_per_1000_ticks", "completed_age_ticks")
LABELS = ("Hazards / move", "Social / decision", "New cells / move", "Children / tick", "Age at death")


def read_csv(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        for k, v in row.items():
            try:
                row[k] = float(v) if v != "" else None
            except ValueError:
                pass
    return rows


def col(rows, name):
    return np.array([r[name] for r in rows], dtype=float)


def quantiles(values):
    values = np.asarray(values)
    if len(values) == 0:
        return dict(n=0, min=None, q10=None, median=None, q90=None, max=None)
    return dict(n=len(values), min=float(min(values)), q10=float(np.quantile(values, .1)),
                median=float(np.median(values)), q90=float(np.quantile(values, .9)), max=float(max(values)))


def km(rows):
    counts = {}
    for a in rows:
        t = int(a["age_ticks"])
        deaths, censored = counts.get(t, (0, 0))
        counts[t] = (deaths+int(a["died"]), censored+int(not a["died"]))
    risk, survival = len(rows), 1.0
    result = [dict(age_ticks=0, risk=risk, deaths=0, censored=0, survival=1.0)]
    for t, (deaths, censored) in sorted(counts.items()):
        survival *= 1 - deaths/risk
        result.append(dict(age_ticks=t, risk=risk, deaths=deaths, censored=censored, survival=survival))
        risk -= deaths+censored
    assert risk == 0
    return result


def figure_save(fig, out, name):
    fig.savefig(out / f"{name}.png", dpi=160, bbox_inches="tight")
    svg = out / f"{name}.svg"
    fig.savefig(svg, bbox_inches="tight", metadata={"Date": "2026-10-19"})
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("research/phase1/data"))
    parser.add_argument("--out", type=Path, default=Path("research/phase1/results"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.alpha": .2, "svg.fonttype": "none", "svg.hashsalt": "gnome-fortress-phase1"})
    summaries, trait_rows, life_rows, sleep_rows, km_rows, dynamics_rows = [], [], [], [], [], []
    all_pop, all_agents, all_sleeps = {}, {}, {}
    fig_pop, axes_pop = plt.subplots(1, 2, figsize=(13, 4.5))
    fig_surv, axes_surv = plt.subplots(2, 2, figsize=(12, 8))
    fig_sched, axes_sched = plt.subplots(1, 2, figsize=(12, 4.5))
    fig_dyn, axes_dyn = plt.subplots(1, 2, figsize=(12, 4.5))
    for path in sorted(args.data.glob("seed-*")):
        summary = json.loads((path / "summary.json").read_text())
        assert summary["ticks"] == 20000, "Phase 1 analysis requires the fixed 20,000-tick horizon"
        seed = summary["seed"]
        color = COLORS[(seed-1) % len(COLORS)]
        pop, agents, sleeps = (read_csv(path / f"{name}.csv") for name in ("population", "agents", "sleep"))
        all_pop[seed], all_agents[seed], all_sleeps[seed] = pop, agents, sleeps
        x, y = col(pop, "tick"), col(pop, "living")
        tail = x >= 10000
        slope, intercept = np.polyfit(x[tail]/1000, y[tail], 1)
        resid = y[tail] - (slope*x[tail]/1000+intercept)
        tail_mean = float(np.mean(y[tail]))
        previous_mean = float(np.mean(y[(x>10000) & (x<=15000)]))
        final_mean = float(np.mean(y[x>15000]))
        total = summary["counters"]
        sums = dict(seed=seed, final_population=summary["living"], total_births=summary["total_births"],
                    offspring=summary["offspring"], deaths=summary["deaths"],
                    **{f"death_{cause}": summary["death_causes"].get(cause, 0) for cause in CAUSES},
                    sampled_peak_population=int(max(y)), tail_mean=tail_mean, tail_min=int(min(y[tail])), tail_max=int(max(y[tail])),
                    tail_slope_per_1000_ticks=float(slope), tail_detrended_cv=float(np.std(resid)/tail_mean),
                    previous_5000_mean=previous_mean, final_5000_mean=final_mean,
                    mean_ratio_final_previous=final_mean/previous_mean,
                    assigned_utilization=total["decisions"]/total["capacity_slot_ticks"],
                    retained_utilization=total["retained_slot_ticks"]/total["capacity_slot_ticks"],
                    eligible_wait_fraction=1-total["decisions"]/total["eligible_agent_ticks"],
                    hazards=total["hazard"], social_interactions=total["social"], final_digest=summary["final_digest"])
        summaries.append(sums)
        axes_pop[0].plot(x, y, color=color, lw=1.1, label=str(seed))
        axes_pop[1].plot(x[tail], y[tail], color=color, lw=1, label=str(seed))
        completed = [a for a in agents if a["died"]]
        offspring = [a for a in agents if not a["founder"]]
        for group, subset in (("founder_completed", [a for a in completed if a["founder"]]),
                              ("offspring_completed", [a for a in completed if not a["founder"]]),
                              ("offspring_right_censored", [a for a in offspring if not a["died"]])):
            life_rows.append(dict(seed=seed, group=group, **quantiles([a["age_ticks"] for a in subset])))
        survival = km(offspring)
        km_rows.extend(dict(seed=seed, **r) for r in survival)
        axes_surv[1, 0].step([r["age_ticks"] for r in survival], [r["survival"] for r in survival],
                             where="post", color=color, lw=1, label=str(seed))
        for status in ("wake", "death", "censored"):
            subset = [s for s in sleeps if s["status"] == status]
            sleep_rows.append(dict(seed=seed, status=status, **quantiles([s["duration_ticks"] for s in subset])))
        cohort = [a for a in offspring if a["born_tick"] <= 17000 and a["decisions"] >= 100]
        assert all(a["died"] for a in cohort), "complete-cohort assumption failed"
        for a in cohort:
            a["hazards_per_100_moves"] = a["hazard_entries"] / a["move"] * 100 if a["move"] else np.nan
            a["social_per_100_decisions"] = a["socialize"] / a["decisions"] * 100
            a["novel_move_fraction"] = a["novel_moves"] / a["move"] if a["move"] else np.nan
            a["parenthood_per_1000_ticks"] = a["children"] / a["observed_ticks"] * 1000
            a["completed_age_ticks"] = a["age_ticks"]
        for trait in TRAITS:
            for metric in METRICS:
                tx, my = col(cohort, trait), col(cohort, metric)
                keep = np.isfinite(tx) & np.isfinite(my)
                rho = float(spearmanr(tx[keep], my[keep]).statistic) if np.std(tx[keep]) and np.std(my[keep]) else np.nan
                trait_rows.append(dict(seed=seed, trait=trait, metric=metric, n=int(sum(keep)), spearman_rho=rho))
        valid = pop[1:]
        tx = col(valid, "tick")
        assigned = col(valid, "decisions") / col(valid, "capacity_slot_ticks")
        retained = col(valid, "retained_slot_ticks") / col(valid, "capacity_slot_ticks")
        waiting = 1-col(valid, "decisions") / col(valid, "eligible_agent_ticks")
        axes_sched[0].plot(tx, assigned*100, color=color, lw=.7, alpha=.65)
        axes_sched[0].plot(tx, retained*100, color=color, lw=.6, ls=":", alpha=.6)
        axes_sched[1].plot(tx, waiting*100, color=color, lw=1, label=str(seed))
        denom = np.dot(resid, resid)
        lags = np.arange(0, 31)
        acf = np.array([np.dot(resid[:len(resid)-lag], resid[lag:])/denom for lag in lags])
        axes_dyn[0].plot(lags*100, acf, color=color, lw=1, label=str(seed))
        frequencies = np.fft.rfftfreq(len(resid), d=100)
        power = abs(np.fft.rfft(resid))**2
        positive = (frequencies >= 1/5000) & (frequencies <= 1/300)
        periods = 1/frequencies[positive]
        normalized_power = power[positive]/sum(power[positive])
        axes_dyn[1].plot(periods, normalized_power, color=color, lw=1)
        for lag, value in zip(lags, acf):
            dynamics_rows.append(dict(seed=seed, lag_ticks=int(lag*100), autocorrelation=float(value)))
        sums["largest_spectral_peak_period_ticks"] = float(periods[np.argmax(normalized_power)])
    write_csv(args.out / "seed_summary.csv", summaries)
    write_csv(args.out / "trait_correlations.csv", trait_rows)
    write_csv(args.out / "lifespans.csv", life_rows)
    write_csv(args.out / "sleep_durations.csv", sleep_rows)
    write_csv(args.out / "offspring_survival.csv", km_rows)
    write_csv(args.out / "autocorrelation.csv", dynamics_rows)
    trait_summary = []
    rho_matrix = np.zeros((len(TRAITS), len(METRICS)))
    for i, trait in enumerate(TRAITS):
        for j, metric in enumerate(METRICS):
            values = [r["spearman_rho"] for r in trait_rows if r["trait"] == trait and r["metric"] == metric]
            rho_matrix[i, j] = np.median(values)
            trait_summary.append(dict(trait=trait, metric=metric, median_rho=float(np.median(values)),
                                      min_rho=float(min(values)), max_rho=float(max(values)), positive_seeds=sum(v>0 for v in values), n_seeds=len(values)))
    write_csv(args.out / "trait_correlation_summary.csv", trait_summary)
    for ax, title in zip(axes_pop, ("Population from 60 founders", "Later population (ticks 10,000–20,000)")):
        ax.set(xlabel="World tick", ylabel="Living gnomes", title=title)
    axes_pop[0].legend(title="Seed", ncol=2, fontsize=8)
    figure_save(fig_pop, args.out, "population")
    bottom = np.zeros(len(summaries))
    for cause, color in zip(CAUSES, ("#577590", "#f8961e", "#43aa8b", "#d1495b")):
        values = np.array([s[f"death_{cause}"]/s["deaths"]*100 for s in summaries])
        axes_surv[0, 0].bar([s["seed"] for s in summaries], values, bottom=bottom, label=cause.replace("_", " "), color=color)
        bottom += values
    axes_surv[0, 0].set(title="Recorded terminal causes", xlabel="Seed", ylabel="Share of deaths (%)", xticks=list(all_pop))
    axes_surv[0, 0].legend(fontsize=8)
    pooled = [a for agents in all_agents.values() for a in agents if not a["founder"] and a["died"]]
    for cause, color in zip(CAUSES, ("#577590", "#f8961e", "#43aa8b", "#d1495b")):
        values = [a["age_ticks"] for a in pooled if a["death_cause"] == cause]
        axes_surv[0, 1].hist(values, bins=np.arange(0, 3101, 100), histtype="step", lw=1.5, label=cause.replace("_", " "), color=color)
    axes_surv[0, 1].set(title="Completed offspring lifespans (pooled)", xlabel="Biological age at death (ticks)", ylabel="Deaths")
    axes_surv[1, 0].set(title="Offspring survival with right censoring", xlabel="Biological age (ticks)", ylabel="Kaplan–Meier survival", ylim=(0, 1.03))
    for status, color in zip(("wake", "death", "censored"), ("#43aa8b", "#d1495b", "#577590")):
        counts = Counter(int(s["duration_ticks"]) for spells in all_sleeps.values() for s in spells if s["status"] == status)
        axes_surv[1, 1].plot(range(13), [counts.get(i, np.nan) for i in range(13)], marker="o", linestyle="none", label=status, color=color)
    axes_surv[1, 1].set(title="Sleep spells by observed end", xlabel="Elapsed sleep ticks", ylabel="Spells (log scale)", yscale="log")
    axes_surv[1, 1].legend(fontsize=8)
    fig_surv.tight_layout()
    figure_save(fig_surv, args.out, "lifecycle")
    axes_sched[0].set(title="Decision capacity used (solid); slots retained (dotted)", xlabel="World tick", ylabel="60-slot capacity used (%)", ylim=(80, 101))
    axes_sched[1].set(title="Awake eligibility opportunities without a slot", xlabel="World tick", ylabel="Eligible opportunities waiting (%)", ylim=(0, 100))
    axes_sched[1].legend(title="Seed", ncol=2, fontsize=8)
    figure_save(fig_sched, args.out, "scheduling")
    axes_dyn[0].axhline(0, color="gray", lw=.7)
    axes_dyn[0].set(title="Detrended later-population autocorrelation", xlabel="Lag (ticks)", ylabel="Autocorrelation")
    axes_dyn[1].set(title="Descriptive later-population spectrum", xlabel="Period (ticks)", ylabel="Normalized power (300–5,000 tick band)")
    figure_save(fig_dyn, args.out, "dynamics")
    fig, ax = plt.subplots(figsize=(10, 5))
    im = ax.imshow(rho_matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set(xticks=range(len(METRICS)), xticklabels=LABELS, yticks=range(len(TRAITS)), yticklabels=TRAITS,
           title="Inherited traits and behavior: median within-seed Spearman correlation\nComplete early-born offspring with ≥100 own decisions; association only")
    ax.grid(False)
    for i in range(len(TRAITS)):
        for j in range(len(METRICS)):
            ax.text(j, i, f"{rho_matrix[i,j]:+.2f}", ha="center", va="center", color="white" if abs(rho_matrix[i,j])>.6 else "black")
    fig.colorbar(im, ax=ax, label="Median correlation across ten seeds")
    figure_save(fig, args.out, "traits")
    pooled_sleep = [s for spells in all_sleeps.values() for s in spells]
    findings = dict(seeds=len(summaries), final_populations=[s["final_population"] for s in summaries],
                    total_births=sum(s["total_births"] for s in summaries), deaths=sum(s["deaths"] for s in summaries),
                    deaths_by_cause={cause: sum(s[f"death_{cause}"] for s in summaries) for cause in CAUSES},
                    offspring_completed_lifespans=quantiles([a["age_ticks"] for a in pooled]),
                    sleep={status: quantiles([s["duration_ticks"] for s in pooled_sleep if s["status"]==status]) for status in ("wake", "death", "censored")},
                    wake_shorter_than_12=sum(s["status"]=="wake" and s["duration_ticks"]<12 for s in pooled_sleep),
                    population_tail_mean=quantiles([s["tail_mean"] for s in summaries]),
                    population_tail_slopes=quantiles([s["tail_slope_per_1000_ticks"] for s in summaries]),
                    late_cv=quantiles([s["tail_detrended_cv"] for s in summaries]))
    (args.out / "findings.json").write_text(json.dumps(findings, indent=2, sort_keys=True)+"\n")
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
