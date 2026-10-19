import csv
import json

import pytest

from gnome_fortress.engine import World
from gnome_fortress.storage import load
from research.study import MeasuredWorld, check_neutrality, run_seed


@pytest.mark.parametrize("seed", [1, 42, 2026])
def test_instrumentation_is_nonintervening(seed):
    assert check_neutrality(seed, 200)["equal"]


def test_sidecar_records_reconcile(tmp_path):
    summary = run_seed(7, 500, 100, tmp_path)
    reference = World(7)
    reference.step(500)
    path = tmp_path / "seed-07"
    assert load(path / "final.sqlite").state() == reference.state()
    assert summary["final_digest"] == reference.digest()
    with (path / "agents.csv").open() as f:
        agents = list(csv.DictReader(f))
    assert len(agents) == len(reference.agents)
    for row in agents:
        assert int(row["age_ticks"]) == int(row["initial_age"]) + int(row["observed_ticks"])
        assert int(row["unique_visited_cells"]) == int(row["novel_moves"])
        assert sum(int(row[k]) for k in ("move", "eat", "drink", "sleep", "socialize", "reproduce", "wait")) == int(row["decisions"])
    assert sum(int(r["hazard_entries"]) for r in agents) == summary["counters"]["hazard"]
    with (path / "population.csv").open() as f:
        population = list(csv.DictReader(f))
    assert all(int(r["living"]) == int(r["births_total"]) - int(r["deaths_total"]) for r in population)
    assert sum(int(r["decisions"]) for r in population) == summary["counters"]["decisions"]
    assert all(int(r["retained_slot_ticks"]) <= int(r["decisions"]) <= int(r["capacity_slot_ticks"]) for r in population)
    with (path / "sleep.csv").open() as f:
        spells = list(csv.DictReader(f))
    assert len(spells) == summary["counters"]["sleep"]
    for r in spells:
        assert int(r["duration_ticks"]) == int(r["end_tick"]) - int(r["start_tick"])
        assert 0 <= int(r["duration_ticks"]) <= 12
