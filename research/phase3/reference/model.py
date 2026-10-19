"""Explicit data; all quantities in integer simulation units."""
from dataclasses import dataclass, field


@dataclass
class Cell:
    terrain: str
    food: int = 0


@dataclass
class Episode:
    tick: int
    action: str
    x: int
    y: int
    feature: str
    reward: int


@dataclass
class Agent:
    id: int
    name: str
    x: int
    y: int
    born: int
    parents: tuple[int, ...]
    traits: dict[str, int]
    age: int = 0
    health: int = 100
    hunger: int = 10
    thirst: int = 10
    fatigue: int = 0
    sleep_until: int = 0
    alive: bool = True
    died: int | None = None
    death_cause: str | None = None
    cooldown: int = 0
    children: int = 0
    action: str = "born"
    memories: list[Episode] = field(default_factory=list)
    learned: dict[str, int] = field(default_factory=dict)
    relationships: dict[int, int] = field(default_factory=dict)
    visits: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    tick: int
    kind: str
    actor: int | None
    target: int | None
    detail: dict
