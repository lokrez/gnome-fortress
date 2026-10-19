"""Atomic SQLite checkpoints with queryable identity, ancestry, memory and events."""
from contextlib import closing
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from .engine import World

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS cells (
    x INTEGER, y INTEGER, terrain TEXT NOT NULL, food INTEGER NOT NULL,
    PRIMARY KEY (x, y));
CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, alive INTEGER NOT NULL,
    born INTEGER NOT NULL, died INTEGER, state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS ancestry (
    child INTEGER REFERENCES agents(id), parent INTEGER REFERENCES agents(id),
    position INTEGER NOT NULL, PRIMARY KEY (child, position));
CREATE TABLE IF NOT EXISTS memories (
    agent INTEGER REFERENCES agents(id), sequence INTEGER, tick INTEGER NOT NULL,
    action TEXT NOT NULL, x INTEGER NOT NULL, y INTEGER NOT NULL,
    feature TEXT NOT NULL, reward INTEGER NOT NULL, PRIMARY KEY (agent, sequence));
CREATE TABLE IF NOT EXISTS relationships (
    source INTEGER REFERENCES agents(id), target INTEGER REFERENCES agents(id),
    value INTEGER NOT NULL, PRIMARY KEY (source, target));
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY, tick INTEGER NOT NULL, kind TEXT NOT NULL,
    actor INTEGER REFERENCES agents(id), target INTEGER REFERENCES agents(id),
    detail TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS events_tick ON events(tick);
CREATE INDEX IF NOT EXISTS events_kind ON events(kind);
"""


def save(world: World, path):
    world.validate()
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript(SCHEMA)
        old = db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if old and old[0] != "1":
            raise ValueError("Unsupported checkpoint schema")
        with db:
            for table in ("ancestry", "memories", "relationships", "events", "agents", "cells", "metadata"):
                db.execute(f"DELETE FROM {table}")
            header = {k: v for k, v in world.state().items() if k not in ("agents", "events", "cells")}
            db.executemany("INSERT INTO metadata VALUES (?, ?)",
                           [("schema_version", "1"), ("world", json.dumps(header))])
            db.executemany("INSERT INTO cells VALUES (?, ?, ?, ?)",
                           ((x, y, c.terrain, c.food) for y, row in enumerate(world.cells) for x, c in enumerate(row)))
            for a in world.agents.values():
                data = asdict(a)
                for key in ("parents", "memories", "relationships"):
                    del data[key]
                db.execute("INSERT INTO agents VALUES (?, ?, ?, ?, ?, ?)",
                           (a.id, a.name, int(a.alive), a.born, a.died, json.dumps(data)))
            for a in world.agents.values():
                db.executemany("INSERT INTO ancestry VALUES (?, ?, ?)",
                               ((a.id, parent, pos) for pos, parent in enumerate(a.parents)))
                db.executemany("INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               ((a.id, i, m.tick, m.action, m.x, m.y, m.feature, m.reward)
                                for i, m in enumerate(a.memories)))
                db.executemany("INSERT INTO relationships VALUES (?, ?, ?)",
                               ((a.id, target, value) for target, value in sorted(a.relationships.items())))
            db.executemany("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                           ((i, e.tick, e.kind, e.actor, e.target, json.dumps(e.detail))
                            for i, e in enumerate(world.events)))


def load(path):
    # Read-only open prevents accidentally creating an empty checkpoint on typo.
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        db.row_factory = sqlite3.Row
        metadata = dict(db.execute("SELECT key, value FROM metadata"))
        if metadata["schema_version"] != "1":
            raise ValueError("Unsupported checkpoint schema")
        data = json.loads(metadata["world"])
        data["cells"] = [[None] * data["width"] for _ in range(data["height"])]
        for c in db.execute("SELECT * FROM cells ORDER BY y, x"):
            data["cells"][c["y"]][c["x"]] = dict(terrain=c["terrain"], food=c["food"])
        agents = {}
        for a in db.execute("SELECT * FROM agents ORDER BY id"):
            item = json.loads(a["state"])
            item.update(parents=[], memories=[], relationships={})
            agents[a["id"]] = item
        for row in db.execute("SELECT * FROM ancestry ORDER BY child, position"):
            agents[row["child"]]["parents"].append(row["parent"])
        for row in db.execute("SELECT * FROM memories ORDER BY agent, sequence"):
            agents[row["agent"]]["memories"].append({k: row[k] for k in ("tick", "action", "x", "y", "feature", "reward")})
        for row in db.execute("SELECT * FROM relationships ORDER BY source, target"):
            agents[row["source"]]["relationships"][row["target"]] = row["value"]
        data["agents"] = list(agents.values())
        data["events"] = [dict(tick=e["tick"], kind=e["kind"], actor=e["actor"],
                               target=e["target"], detail=json.loads(e["detail"]))
                          for e in db.execute("SELECT * FROM events ORDER BY sequence")]
    world = World.from_state(data)
    world.validate()
    return world
