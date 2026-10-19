"""Experiment-only controls; original source and default remain untouched.

Capacity uses a process-scoped context around the baseline module constant. Never
run different capacities concurrently in threads. Scientific parallelism uses
separate processes, and experiment checkpoints carry an external configuration.
"""
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import asdict, dataclass
import hashlib
import json
import time

from gnome_fortress import engine
from gnome_fortress.engine import World
from gnome_fortress.storage import load, save

CAPACITIES = (60, 120, 240, 480, 960)


@dataclass(frozen=True)
class Config:
    slots: int = 60
    memory: str = "enabled"

    def __post_init__(self):
        if self.slots not in CAPACITIES or self.memory not in ("enabled", "ablated"):
            raise ValueError("Unsupported experimental configuration")


@contextmanager
def capacity(slots):
    Config(slots=slots)
    previous = engine.SLOTS
    engine.SLOTS = slots
    try:
        yield
    finally:
        engine.SLOTS = previous


class BlindReadout(dict):
    """Retain the complete table, but mask movement values for policy readout."""
    blind = True

    def get(self, key, default=None):
        if self.blind and key.startswith("move:"):
            return 0
        return super().get(key, default)


class ExperimentalWorld(World):
    def __init__(self, seed=1, config=Config()):
        self.config = config
        self.generations = {}
        self.metrics = defaultdict(Counter)
        self.measured = Counter()
        self.assigned = self.eligible = 0
        super().__init__(seed)
        assert len(self.slots) == config.slots == engine.SLOTS
        self.initial_ages = {a.id: a.age for a in self.agents.values()}

    @classmethod
    def adopt(cls, world, config):
        assert len(world.slots) == config.slots == engine.SLOTS
        world.__class__ = cls
        world.config = config
        world.generations = {}
        for a in world.agents.values():
            world.generations[a.id] = 0 if not a.parents else 1 + max(world.generations[p] for p in a.parents)
        world.metrics = defaultdict(Counter)
        world.measured = Counter()
        world.assigned = world.eligible = 0
        world.initial_ages = {a.id: a.age-(a.died if a.died is not None else world.tick)
                              for a in world.agents.values() if not a.parents}
        return world

    def _spawn(self, x, y, traits, parents, age=0):
        a = super()._spawn(x, y, traits, parents, age)
        self.generations[a.id] = 0 if not parents else 1+max(self.generations[p] for p in parents)
        return a

    def schedule(self):
        start = time.perf_counter_ns()
        chosen = super().schedule()
        self.measured["scheduler_ns"] += time.perf_counter_ns()-start
        self.assigned = len(chosen)
        self.eligible = sum(a.alive and a.sleep_until <= self.tick for a in self.agents.values())
        return chosen

    def move(self, a):
        if self.config.memory == "enabled":
            return super().move(a)
        original = a.learned
        table = BlindReadout(original)
        a.learned = table
        try:
            return super().move(a)
        finally:
            # Consequence updates are retained even in the ablated condition.
            original.clear()
            original.update(table)
            a.learned = original

    def remember(self, a, action, feature, reward):
        table = a.learned
        if isinstance(table, BlindReadout):
            table.blind = False
        try:
            super().remember(a, action, feature, reward)
        finally:
            if isinstance(table, BlindReadout):
                table.blind = True
        if action == "eat":
            self.measured["food_consumed"] += reward

    def decide(self, a):
        position, visited = (a.x, a.y), len(a.visits)
        super().decide(a)
        action = "move" if not a.alive and position != (a.x, a.y) else a.action
        m = self.metrics[a.id]
        m["decisions"] += 1
        m[action] += 1
        if action == "move":
            m["novel_moves"] += int(len(a.visits) > visited)
            m["hazard_entries"] += int(self.cell(a.x, a.y).terrain == "hazard")


def biological_digest(world):
    data = world.state()
    del data["slots"]  # Only initial capacity's empty slot-array length differs.
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save_experiment(world, path):
    save(world, path)
    path.with_suffix(".config.json").write_text(json.dumps(asdict(world.config), sort_keys=True)+"\n")


def load_experiment(path, expected=None):
    config = Config(**json.loads(path.with_suffix(".config.json").read_text()))
    if expected is not None and expected != config:
        raise ValueError("Checkpoint treatment/capacity mismatch")
    assert engine.SLOTS == config.slots, "Enter the matching capacity context before load"
    return ExperimentalWorld.adopt(load(path), config)
