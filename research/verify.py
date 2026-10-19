"""Cross-check all telemetry against final archives and replay one full baseline."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import json
from pathlib import Path
import time

from gnome_fortress.engine import World
from gnome_fortress.storage import load
from research.study import write_csv

DATA = Path("research/phase1/data")
OUT = Path("research/phase1/results")


def check_seed(seed):
    path = DATA / f"seed-{seed:02d}"
    summary = json.loads((path / "summary.json").read_text())
    w = load(path / "final.sqlite")
    assert w.digest() == summary["final_digest"]
    events = Counter(e.kind for e in w.events)
    assert events["birth"] == len(w.agents) == summary["total_births"]
    assert events["death"] == summary["deaths"]
    assert events["hazard"] == summary["counters"]["hazard"]
    changes = [0] * (w.tick+1)
    for e in w.events:
        if e.kind == "birth":
            changes[e.tick] += 1
        elif e.kind == "death":
            changes[e.tick] -= 1
    population = []
    stock = 0
    for change in changes:
        stock += change
        population.append(stock)
    assert population[0] == 60 and population[-1] == len(w.living())
    with (path / "population.csv").open() as f:
        for row in csv.DictReader(f):
            assert int(row["living"]) == population[int(row["tick"])]
    with (path / "agents.csv").open() as f:
        agents = list(csv.DictReader(f))
    assert len(agents) == len(w.agents)
    for row in agents:
        a = w.agents[int(row["agent"])]
        assert int(row["children"]) == a.children
        assert int(row["age_ticks"]) == a.age
        assert int(row["died"]) == int(not a.alive)
    assert sum(int(row["children"]) for row in agents) == 2 * (len(agents)-60)
    assert sum(int(row["decisions"]) for row in agents) == summary["counters"]["decisions"]
    assert sum(int(row["hazard_entries"]) for row in agents) == events["hazard"]
    return dict(seed=seed, all_tick_min=min(population), exact_peak=max(population),
                first_peak_tick=population.index(max(population)),
                tail_exact_min=min(population[10000:]), tail_exact_max=max(population[10000:]),
                extinct_ticks=sum(p == 0 for p in population),
                checkpoint_digest_matches=True, population_samples_match=True,
                ancestry_and_population_valid=True)


def main():
    start = time.monotonic()
    with ProcessPoolExecutor(max_workers=4) as pool:
        checks = list(pool.map(check_seed, range(1, 11)))
    write_csv(OUT / "exact_population_checks.csv", checks)
    print("All ten archives and telemetry reconcile", flush=True)
    w = World(1)
    w.step(20000)
    summary = json.loads((DATA / "seed-01/summary.json").read_text())
    assert w.digest() == summary["final_digest"]
    result = dict(archive_checks=checks, independent_uninstrumented_replay=dict(seed=1, ticks=20000,
                 expected_digest=summary["final_digest"], actual_digest=w.digest(), equal=True),
                 seconds=round(time.monotonic()-start, 3))
    (OUT / "verification.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps(result["independent_uninstrumented_replay"], indent=2), flush=True)


if __name__ == "__main__":
    main()
