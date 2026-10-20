"""Simulation only: no wall clock, renderer, database, or global random state."""
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import random

from .model import Agent, Cell, Episode, Event

SLOTS = 60
TRAITS = ("curiosity", "caution", "sociability", "fertility", "stamina", "vision")


class World:
    def __init__(self, seed: int = 1, width: int = 48, height: int = 32):
        if width < 8 or height < 8:
            raise ValueError("World must be at least 8 by 8")
        self.seed, self.width, self.height = seed, width, height
        self.rng = random.Random(seed)
        self.tick = 0
        self.next_id = 1
        self.cursor = 0
        self.slots: list[int | None] = [None] * SLOTS
        self.agents: dict[int, Agent] = {}
        self._living_agents: dict[int, Agent] = {}
        self.events: list[Event] = []
        self.cells: list[list[Cell]] = []
        for y in range(height):
            row = []
            for x in range(width):
                roll = self.rng.randrange(100)
                terrain = ("water" if roll < 9 else "rock" if roll < 15 else
                           "hazard" if roll < 20 else "forest" if roll < 45 else "grass")
                row.append(Cell(terrain, self.rng.randrange(30, 101) if terrain == "forest" else
                                self.rng.randrange(10, 61) if terrain == "grass" else 0))
            self.cells.append(row)
        # Guarantee basic resources and a traversable founder nursery for every seed.
        for y in range(1, 7):
            for x in range(1, 7):
                self.cells[y][x] = Cell("grass", 100)
        self.cells[3][3] = Cell("water")
        safe = [(x, y) for y in range(height) for x in range(width)
                if self.cells[y][x].terrain in ("grass", "forest")]
        for _ in range(60):
            x, y = self.rng.choice(safe)
            traits = {k: self.rng.randint(20, 80) for k in TRAITS}
            self._spawn(x, y, traits, (), age=self.rng.randint(120, 300))

    def event(self, kind, actor=None, target=None, **detail):
        self.events.append(Event(self.tick, kind, actor, target, detail))

    def _spawn(self, x, y, traits, parents, age=0):
        identity = self.next_id
        self.next_id += 1
        agent = Agent(identity, f"Gnome {identity:05d}", x, y, self.tick,
                      tuple(parents), dict(traits), age=age)
        self.agents[identity] = agent
        self._living_agents[identity] = agent
        self.event("birth", identity, parents=list(parents), founder=not parents)
        return agent

    def living(self):
        return list(self._living_agents.values())

    def cell(self, x, y):
        return self.cells[y][x]

    def neighbors(self, x, y):
        # Stable north/east/south/west ordering is part of the simulation contract.
        return [(nx, ny) for nx, ny in ((x, y-1), (x+1, y), (x, y+1), (x-1, y))
                if 0 <= nx < self.width and 0 <= ny < self.height]

    def observations(self, a):
        radius = 3 + a.traits["vision"] // 25
        return [(x, y) for y in range(max(0, a.y-radius), min(self.height, a.y+radius+1))
                for x in range(max(0, a.x-radius), min(self.width, a.x+radius+1))
                if abs(x-a.x) + abs(y-a.y) <= radius]

    def remember(self, a, action, feature, reward):
        a.memories.append(Episode(self.tick, action, a.x, a.y, feature, reward))
        del a.memories[:-64]
        # Incremental association, updated only by an experienced consequence.
        key = f"{action}:{feature}"
        a.learned[key] = max(-100, min(100, (3 * a.learned.get(key, 0) + reward) // 4))

    def kill(self, a, cause):
        if not a.alive:
            return
        a.alive, a.died, a.death_cause, a.action = False, self.tick, cause, "dead"
        self._living_agents.pop(a.id, None)
        self.slots = [None if identity == a.id else identity for identity in self.slots]
        self.event("death", a.id, cause=cause, age=a.age)

    def _biology(self, a):
        a.age += 1
        a.cooldown = max(0, a.cooldown - 1)
        a.hunger += 1
        a.thirst += 2
        if a.sleep_until > self.tick:
            a.fatigue = max(0, a.fatigue - 6)
            if a.hunger >= 85 or a.thirst >= 85:
                a.sleep_until = self.tick
        else:
            a.fatigue = min(130, a.fatigue + 1)
        damage = (2 if a.hunger > 100 else 0) + (3 if a.thirst > 100 else 0)
        a.health -= damage
        a.hunger, a.thirst = min(150, a.hunger), min(150, a.thirst)
        if not damage and a.hunger < 60 and a.thirst < 60 and self.tick % 5 == 0:
            a.health = min(100, a.health + 1)
        if a.health <= 0:
            self.kill(a, "dehydration" if a.thirst > 100 else "starvation")
        elif a.age >= 1800 + a.traits["stamina"] * 12:
            self.kill(a, "old_age")

    def schedule(self):
        eligible = sorted(a.id for a in self._living_agents.values()
                          if a.alive and a.sleep_until <= self.tick)
        # Rotate by identity, not list position: births/deaths cannot reset fairness.
        ordered = [i for i in eligible if i > self.cursor] + [i for i in eligible if i <= self.cursor]
        chosen = ordered[:SLOTS]
        self.slots = chosen + [None] * (SLOTS - len(chosen))
        if chosen:
            self.cursor = chosen[-1]
        return chosen

    def step(self, count=1):
        for _ in range(count):
            self.tick += 1
            if self.tick % 10 == 0:
                self._regenerate_food()
            for a in list(self._living_agents.values()):
                if a.alive:
                    was_asleep = a.sleep_until > self.tick - 1
                    self._biology(a)
                    if a.alive and was_asleep and a.sleep_until <= self.tick:
                        self.event("wake", a.id)
            for identity in self.schedule():
                a = self.agents[identity]
                if a.alive:
                    self.decide(a)
            # Sleep immediately relinquishes its slot; births enter next tick.
            self.slots = [i if i is not None and self.agents[i].alive and
                          self.agents[i].sleep_until <= self.tick else None for i in self.slots]

    def _regenerate_food(self):
        """Default resource pulse; opt-in worlds may override environmental effects."""
        for row in self.cells:
            for c in row:
                if c.terrain in ("grass", "forest"):
                    c.food = min(100, c.food + (8 if c.terrain == "forest" else 4))

    def _drinkable(self, x, y):
        return any(self.cell(nx, ny).terrain == "water"
                   for nx, ny in [(x, y)] + self.neighbors(x, y))

    def _nearby_agents(self, a):
        return [b for b in self._living_agents.values() if b.id != a.id and b.alive
                and b.sleep_until <= self.tick and abs(a.x-b.x) + abs(a.y-b.y) <= 1]

    def decide(self, a):
        if a.thirst >= 30 and self._drinkable(a.x, a.y):
            a.thirst = max(0, a.thirst - 70)
            a.action = "drink"
            self.remember(a, "drink", "water", 60)
            return
        c = self.cell(a.x, a.y)
        if a.hunger >= 30 and c.food >= 10:
            portion = min(45, c.food)
            c.food -= portion
            a.hunger = max(0, a.hunger - portion)
            a.action = "eat"
            self.remember(a, "eat", c.terrain, portion)
            return
        if a.fatigue >= 65 and a.hunger < 80 and a.thirst < 75:
            a.sleep_until = self.tick + 12
            a.action = "sleep"
            self.event("sleep", a.id, until=a.sleep_until)
            return
        nearby = self._nearby_agents(a)
        if a.age >= 180 and a.cooldown == 0 and a.health >= 70 and a.hunger < 60 and a.thirst < 60:
            for b in nearby:
                if (b.age >= 180 and b.cooldown == 0 and b.health >= 70 and
                        b.hunger < 60 and b.thirst < 60 and
                        self.rng.randrange(1000) < (a.traits["fertility"] + b.traits["fertility"]) // 3):
                    traits = {k: max(0, min(100, (a.traits[k] + b.traits[k]) // 2 + self.rng.randint(-10, 10)))
                              for k in TRAITS}
                    child = self._spawn(a.x, a.y, traits, (a.id, b.id))
                    for parent, other in ((a, b), (b, a)):
                        parent.cooldown = 240
                        parent.hunger += 20
                        parent.fatigue += 15
                        parent.children += 1
                        parent.relationships[other.id] = min(100, parent.relationships.get(other.id, 0) + 8)
                    a.action = "reproduce"
                    self.event("reproduce", a.id, b.id, child=child.id)
                    self.remember(a, "reproduce", "peer", -20)
                    return
        if nearby and a.hunger < 65 and a.thirst < 65 and self.rng.randrange(100) < a.traits["sociability"] // 5:
            b = nearby[self.rng.randrange(len(nearby))]
            reward = 2 + a.traits["sociability"] // 20
            a.relationships[b.id] = min(100, a.relationships.get(b.id, 0) + reward)
            # The receiving agent values the encounter according to its own trait.
            b.relationships[a.id] = min(100, b.relationships.get(a.id, 0) + 1 + b.traits["sociability"] // 40)
            a.action = "socialize"
            self.remember(a, "socialize", "peer", reward)
            self.event("social", a.id, b.id, reward=reward)
            return
        self.move(a)

    def move(self, a):
        observed = self.observations(a)
        food = [(x, y) for x, y in observed if self.cell(x, y).food >= 10]
        water = [(x, y) for x, y in observed if self.cell(x, y).terrain == "water"]
        peers = [(b.x, b.y) for b in self._nearby_agents(a)]
        candidates = []
        for x, y in self.neighbors(a.x, a.y):
            cell = self.cell(x, y)
            if cell.terrain in ("rock", "water"):
                continue
            visits = a.visits.get(f"{x},{y}", 0)
            score = a.traits["curiosity"] // 4 if visits == 0 else -min(50, visits * 8)
            for targets, weight in ((food, a.hunger), (water, a.thirst * 2)):
                if targets:
                    before = min(abs(tx-a.x) + abs(ty-a.y) for tx, ty in targets)
                    after = min(abs(tx-x) + abs(ty-y) for tx, ty in targets)
                    score += (before-after) * weight
            if peers and a.hunger < 50 and a.thirst < 50:
                score += (2 - min(abs(px-x) + abs(py-y) for px, py in peers)) * a.traits["sociability"] // 10
            if cell.terrain == "hazard":
                score -= a.traits["caution"] // 5  # Inherited tendency; not learning.
            score += a.learned.get(f"move:{cell.terrain}", 0)
            candidates.append((score, x, y))
        if not candidates:
            a.action = "wait"
            return
        best = max(score for score, _, _ in candidates)
        _, a.x, a.y = self.rng.choice([c for c in candidates if c[0] == best])
        key = f"{a.x},{a.y}"
        a.visits[key] = a.visits.get(key, 0) + 1
        a.action = "move"
        terrain = self.cell(a.x, a.y).terrain
        if terrain == "hazard":
            damage = self.rng.randint(12, 30)
            a.health -= damage
            self.remember(a, "move", terrain, -damage * 3)
            self.event("hazard", a.id, damage=damage, x=a.x, y=a.y)
            if a.health <= 0:
                self.kill(a, "hazard")
        else:
            self.remember(a, "move", terrain, 0)

    def state(self):
        return dict(version=1, seed=self.seed, width=self.width, height=self.height,
                    tick=self.tick, next_id=self.next_id, cursor=self.cursor,
                    slots=self.slots, rng=self.rng.getstate(),
                    cells=[[asdict(c) for c in row] for row in self.cells],
                    agents=[asdict(a) for a in self.agents.values()],
                    events=[asdict(e) for e in self.events])

    @classmethod
    def from_state(cls, data):
        if data["version"] != 1:
            raise ValueError("Unsupported simulation version")
        world = cls.__new__(cls)
        for key in ("seed", "width", "height", "tick", "next_id", "cursor", "slots"):
            setattr(world, key, data[key])
        def tuples(value):
            return tuple(tuples(v) for v in value) if isinstance(value, (tuple, list)) else value
        world.rng = random.Random()
        world.rng.setstate(tuples(data["rng"]))
        world.cells = [[Cell(**c) for c in row] for row in data["cells"]]
        world.agents = {}
        for item in data["agents"]:
            item = dict(item)
            item["parents"] = tuple(item["parents"])
            item["relationships"] = {int(k): v for k, v in item["relationships"].items()}
            item["memories"] = [Episode(**m) for m in item["memories"]]
            agent = Agent(**item)
            world.agents[agent.id] = agent
        world.events = [Event(**e) for e in data["events"]]
        world._rebuild_index()
        return world

    def _rebuild_index(self):
        """Derived insertion-ordered references; coordinates remain authoritative."""
        self._living_agents = {i: a for i, a in self.agents.items() if a.alive}

    def digest(self):
        return hashlib.sha256(json.dumps(self.state(), sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def summary(self):
        counts = Counter(e.kind for e in self.events)
        return dict(tick=self.tick, living=len(self.living()), born=len(self.agents),
                    dead=sum(not a.alive for a in self.agents.values()),
                    events=dict(sorted(counts.items())))

    def validate(self):
        assert list(self._living_agents) == [i for i, a in self.agents.items() if a.alive]
        assert all(self.agents[i] is a for i, a in self._living_agents.items())
        assigned = [i for i in self.slots if i is not None]
        assert len(self.slots) == SLOTS and len(assigned) == len(set(assigned))
        assert all(self.agents[i].alive and self.agents[i].sleep_until <= self.tick for i in assigned)
        assert self.next_id == len(self.agents) + 1
        assert sum(not a.parents for a in self.agents.values()) == 60
        births = [e.actor for e in self.events if e.kind == "birth"]
        deaths = [e.actor for e in self.events if e.kind == "death"]
        assert births == list(self.agents) and len(deaths) == len(set(deaths))
        assert set(deaths) == {a.id for a in self.agents.values() if not a.alive}
        for a in self.agents.values():
            assert 0 <= a.x < self.width and 0 <= a.y < self.height
            assert self.cell(a.x, a.y).terrain not in ("rock", "water")
            assert len(a.memories) <= 64
            assert all(0 <= v <= 100 for v in a.traits.values())
            assert len(a.parents) in (0, 2) and len(set(a.parents)) == len(a.parents)
            assert all(p < a.id and p in self.agents and self.agents[p].born <= a.born for p in a.parents)
            assert a.alive == (a.died is None)
