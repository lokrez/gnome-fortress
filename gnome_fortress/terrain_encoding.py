"""The existing canonical JSON, without recursively duplicating the record graph.

Only serialize a stopped owner or detached worker world. Never send this shallow
projection across a thread/process boundary while its source can advance.
"""
from dataclasses import fields, is_dataclass
from functools import lru_cache
import json

from .terrain_game import FORMAT, RECORD_VERSION, TerrainWorld


@lru_cache(maxsize=32)
def _field_names(cls):
    return tuple(f.name for f in fields(cls))


def _record(value):
    if is_dataclass(value) and not isinstance(value, type):
        return {name: getattr(value, name) for name in _field_names(type(value))}
    raise TypeError(f'Object of type {type(value).__name__} is not JSON serializable')


def canonical_payload(world):
    if type(world) is not TerrainWorld:
        # Preserve any explicitly extended state contract instead of dropping it.
        return json.dumps(world.state(), sort_keys=True, separators=(',', ':'))
    data = dict(version=1, seed=world.seed, width=world.width, height=world.height,
                tick=world.tick, next_id=world.next_id, cursor=world.cursor,
                slots=world.slots, rng=world.rng.getstate(), cells=world.cells,
                agents=list(world.agents.values()), events=world.events,
                game=dict(format=FORMAT, record_version=RECORD_VERSION,
                          interventions=world.interventions,
                          extinct_tick=world.extinct_tick,
                          initial_terrain=world.initial_terrain, origin=world.origin))
    return json.dumps(data, default=_record, sort_keys=True, separators=(',', ':'))
