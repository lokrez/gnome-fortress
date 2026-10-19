"""Non-intervening phase-1 measurement. Run with python -m research.study."""
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import time

from gnome_fortress.engine import World, SLOTS, TRAITS
from gnome_fortress.storage import save

BASELINE = "f32c1a6"


def write_csv(path, rows, fields=None):
    iterator = iter(rows)
    first = next(iterator, None)
    fields = fields or (list(first) if first is not None else [])
    with Path(path).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        if first is not None:
            writer.writerow(first)
        writer.writerows(iterator)


class MeasuredWorld(World):
    """Sidecar counters. Delegation preserves the exact original update order."""
    def __init__(self, seed):
        super().__init__(seed)
        self.metrics = defaultdict(Counter)
        self.assigned = self.eligible = 0
        self.initial_ages = {a.id: a.age for a in self.agents.values()}

    def schedule(self):
        chosen = super().schedule()
        self.assigned = len(chosen)
        self.eligible = sum(a.alive and a.sleep_until <= self.tick for a in self.agents.values())
        return chosen

    def decide(self, a):
        previous_position = (a.x, a.y)
        nvisits = len(a.visits)
        super().decide(a)
        # A fatal move changes action to 'dead'. Recover the decision, not last label.
        action = "move" if not a.alive and (a.x, a.y) != previous_position else a.action
        m = self.metrics[a.id]
        m["decisions"] += 1
        m[action] += 1
        if action == "move":
            m["novel_moves"] += int(len(a.visits) > nvisits)
            m["hazard_entries"] += int(self.cell(a.x, a.y).terrain == "hazard")


def check_neutrality(seed=1, ticks=500):
    baseline, measured = World(seed), MeasuredWorld(seed)
    for _ in range(ticks):
        baseline.step()
        measured.step()
    assert baseline.state() == measured.state(), "measurement changed baseline"
    return {"seed": seed, "ticks": ticks, "digest": baseline.digest(), "equal": True}


def run_seed(seed, horizon, sample, root):
    start = time.monotonic()
    path = Path(root) / f"seed-{seed:02d}"
    path.mkdir(parents=True, exist_ok=False)
    w = MeasuredWorld(seed)
    initial_digest = w.digest()
    event_index = len(w.events)
    living, births, deaths = 60, 60, 0
    totals, interval = Counter(), Counter()
    death_causes = Counter()
    sleeps = {}
    sleep_count = Counter()
    sleep_file = (path / "sleep.csv").open("w", newline="")
    sleep_writer = csv.DictWriter(sleep_file, fieldnames=["seed", "agent", "start_tick", "planned_end_tick", "end_tick", "duration_ticks", "status"])
    sleep_writer.writeheader()

    def end_sleep(identity, tick, status):
        if identity in sleeps:
            begin, until = sleeps.pop(identity)
            sleep_writer.writerow(dict(seed=seed, agent=identity, start_tick=begin,
                                       planned_end_tick=until, end_tick=tick,
                                       duration_ticks=tick-begin, status=status))
            sleep_count[status] += 1

    rows = [dict(seed=seed, tick=0, living=60, births_total=60, deaths_total=0,
                 births_interval=0, deaths_interval=0, eligible_agent_ticks=0,
                 decisions=0, retained_slot_ticks=0, capacity_slot_ticks=0,
                 sleeping=0, hazards=0, social=0)]
    for tick in range(1, horizon + 1):
        w.step()
        for event in w.events[event_index:]:
            totals[event.kind] += 1
            interval[event.kind] += 1
            if event.kind == "birth":
                births += 1
                living += 1
            elif event.kind == "death":
                deaths += 1
                living -= 1
                death_causes[event.detail["cause"]] += 1
                end_sleep(event.actor, tick, "death")
            elif event.kind == "sleep":
                assert event.actor not in sleeps
                sleeps[event.actor] = (tick, event.detail["until"])
            elif event.kind == "wake":
                end_sleep(event.actor, tick, "wake")
        event_index = len(w.events)
        retained = sum(identity is not None for identity in w.slots)
        for counter in (totals, interval):
            counter["eligible_agent_ticks"] += w.eligible
            counter["decisions"] += w.assigned
            counter["retained_slot_ticks"] += retained
            counter["capacity_slot_ticks"] += SLOTS
        if tick % sample == 0 or tick == horizon:
            rows.append(dict(seed=seed, tick=tick, living=living, births_total=births,
                             deaths_total=deaths, births_interval=interval["birth"],
                             deaths_interval=interval["death"], eligible_agent_ticks=interval["eligible_agent_ticks"],
                             decisions=interval["decisions"], retained_slot_ticks=interval["retained_slot_ticks"],
                             capacity_slot_ticks=interval["capacity_slot_ticks"], sleeping=len(sleeps),
                             hazards=interval["hazard"], social=interval["social"]))
            interval.clear()
        if tick % 1000 == 0:
            w.validate()
            assert living == len(w.living()) == births-deaths
        if tick % 5000 == 0:
            print(f"seed={seed} tick={tick} living={living} born={births}", flush=True)
    for identity in list(sleeps):
        end_sleep(identity, horizon, "censored")
    sleep_file.close()
    write_csv(path / "population.csv", rows)
    agent_rows = []
    for a in w.agents.values():
        m = w.metrics[a.id]
        agent_rows.append(dict(seed=seed, agent=a.id, founder=int(not a.parents),
                               parent1=a.parents[0] if a.parents else "",
                               parent2=a.parents[1] if a.parents else "", born_tick=a.born,
                               initial_age=w.initial_ages.get(a.id, 0),
                               end_tick=a.died if a.died is not None else horizon,
                               age_ticks=a.age, observed_ticks=(a.died if a.died is not None else horizon)-a.born,
                               died=int(not a.alive), death_cause=a.death_cause or "",
                               children=a.children, unique_visited_cells=len(a.visits),
                               **a.traits, **{k: m[k] for k in ("decisions", "move", "eat", "drink", "sleep", "socialize", "reproduce", "wait", "novel_moves", "hazard_entries")}))
    write_csv(path / "agents.csv", agent_rows)
    assert sum(r["decisions"] for r in agent_rows) == totals["decisions"]
    summary = dict(seed=seed, ticks=horizon, living=living, total_births=births,
                   offspring=births-60, deaths=deaths, death_causes=dict(death_causes),
                   initial_digest=initial_digest, final_digest=w.digest(), counters=dict(totals),
                   sleep_status=dict(sleep_count), python=platform.python_version())
    (path / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    save(w, path / "final.sqlite")
    (path / "execution.json").write_text(json.dumps(dict(seconds=round(time.monotonic()-start, 3)), indent=2) + "\n")
    print(f"COMPLETE seed={seed} living={living} deaths={deaths}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(1, 11)))
    parser.add_argument("--ticks", type=int, default=20000)
    parser.add_argument("--sample", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, default=Path("research/phase1/data"))
    args = parser.parse_args()
    if args.ticks < 1 or args.sample < 1 or len(set(args.seeds)) != len(args.seeds):
        parser.error("positive ticks/sample and distinct seeds required")
    args.out.mkdir(parents=True, exist_ok=True)
    # Refuse to silently measure a different engine, data model, or checkpoint format.
    for name in ("engine.py", "model.py", "storage.py", "viewer.py", "__main__.py", "__init__.py"):
        original = subprocess.check_output(["git", "show", f"{BASELINE}:gnome_fortress/{name}"])
        assert original == (Path("gnome_fortress") / name).read_bytes(), f"baseline changed: {name}"
    manifest = dict(baseline=subprocess.check_output(["git", "rev-parse", BASELINE], text=True).strip(),
                    seeds=args.seeds, ticks=args.ticks, sample_ticks=args.sample, workers=args.workers,
                    neutrality=check_neutrality(), protocol_sha256=hashlib.sha256(Path("research/phase1/PROTOCOL.md").read_bytes()).hexdigest(),
                    harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), python=platform.python_version())
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(run_seed, seed, args.ticks, args.sample, str(args.out)) for seed in args.seeds]
        results = [job.result() for job in as_completed(jobs)]
    (args.out / "summaries.json").write_text(json.dumps(sorted(results, key=lambda r: r["seed"]), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
