"""Opt-in Phase 4A experiment; the verified World implementation stays untouched."""
from contextlib import closing
import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from .engine import World
from .model import Episode

CONDITIONS = ('individual', 'social', 'sham')


@dataclass(frozen=True)
class CommunicationConfig:
    condition: str = 'individual'

    def __post_init__(self):
        if self.condition not in CONDITIONS:
            raise ValueError(f'Unknown communication condition: {self.condition}')


def origin_record():
    return dict(firsthand_count=0, social_count=0, last_firsthand_tick=None,
                last_social_tick=None, last_source=None)


class CommunicationWorld(World):
    """Only existing socialize decisions can carry a message. No extra RNG calls."""
    def __init__(self, seed=1, config=CommunicationConfig()):
        self.config = config
        self.origins = {}
        self.opportunities = self.messages = self.decision_count = 0
        self.hook_seconds = 0.0  # operational measurement; excluded from state
        super().__init__(seed)

    def remember(self, agent, action, feature, reward):
        super().remember(agent, action, feature, reward)
        origin = self.origins.setdefault(agent.id, {}).setdefault(f'{action}:{feature}', origin_record())
        origin['firsthand_count'] += 1
        origin['last_firsthand_tick'] = self.tick

    def decide(self, agent):
        self.decision_count += 1
        before = len(self.events)
        super().decide(agent)
        started = time.perf_counter()
        try:
            # The existing social event specifies the actual partner. Do not
            # search for additional contacts or consume a separate random draw.
            if len(self.events) > before:
                event = self.events[-1]
                if event.kind == 'social' and event.actor == agent.id:
                    self.contact(agent, self.agents[event.target])
        finally:
            self.hook_seconds += time.perf_counter() - started

    def contact(self, sender, recipient):
        """A controlled contact hook; normal execution calls it only after social."""
        key = 'move:hazard'
        source = self.origins.get(sender.id, {}).get(key, {})
        target = self.origins.get(recipient.id, {}).get(key, {})
        if (not sender.alive or not recipient.alive or sender.id == recipient.id or
                sender.sleep_until > self.tick or recipient.sleep_until > self.tick or
                abs(sender.x-recipient.x) + abs(sender.y-recipient.y) > 1 or
                not source.get('firsthand_count', 0) or
                target.get('firsthand_count', 0) or sender.learned.get(key, 0) >= 0):
            return False
        self.opportunities += 1
        if self.config.condition == 'individual':
            return False
        meaningful = self.config.condition == 'social'
        old = recipient.learned.get(key, 0)
        # This is bounded association strength, NOT a probability of truth.
        # Attenuate the reported value, then use the existing EMA weight.
        transmitted = sender.learned[key] // 2 if meaningful else 0
        if meaningful:
            recipient.learned[key] = max(-100, min(100, (3 * old + transmitted) // 4))
            origin = self.origins.setdefault(recipient.id, {}).setdefault(key, origin_record())
            origin['social_count'] += 1
            origin['last_social_tick'] = self.tick
            origin['last_source'] = sender.id
        recipient.memories.append(Episode(self.tick, 'hear', recipient.x, recipient.y,
                                          'hazard' if meaningful else 'masked', transmitted))
        del recipient.memories[:-64]
        self.messages += 1
        self.event('communication', sender.id, recipient.id,
                   condition=self.config.condition, meaningful=meaningful,
                   key=key if meaningful else None,
                   source_value=sender.learned[key] if meaningful else None,
                   transmitted=transmitted if meaningful else None,
                   previous=old if meaningful else None,
                   updated=recipient.learned[key] if meaningful else None,
                   source_firsthand_count=source['firsthand_count'],
                   source_last_firsthand_tick=source['last_firsthand_tick'])
        return True

    def state(self):
        data = super().state()
        data['communication'] = dict(version=1, config=asdict(self.config),
                                     origins={identity: {key: dict(record) for key, record in records.items()}
                                              for identity, records in self.origins.items()},
                                     opportunities=self.opportunities, messages=self.messages,
                                     decision_count=self.decision_count)
        return data

    @classmethod
    def from_state(cls, data):
        extra = data['communication']
        if extra['version'] != 1:
            raise ValueError('Unsupported communication experiment version')
        world = super().from_state(copy.deepcopy(data))
        world.config = CommunicationConfig(**extra['config'])
        world.origins = {int(identity): {key: dict(record) for key, record in records.items()}
                         for identity, records in extra['origins'].items()}
        world.opportunities = extra['opportunities']
        world.messages = extra['messages']
        world.decision_count = extra['decision_count']
        world.hook_seconds = 0.0
        world.validate()
        return world

    def validate(self):
        super().validate()
        for identity, records in self.origins.items():
            if identity not in self.agents:
                raise ValueError('Unknown knowledge owner')
            for key, origin in records.items():
                if key not in self.agents[identity].learned:
                    raise ValueError('Provenance without learned association')
                if origin['firsthand_count'] < 0 or origin['social_count'] < 0:
                    raise ValueError('Invalid provenance counts')
                if origin['last_source'] is not None and origin['last_source'] not in self.agents:
                    raise ValueError('Unknown knowledge source')


def save_experiment(world, path):
    """Separate atomic/checksummed format; never overwrite a baseline checkpoint."""
    if not isinstance(world, CommunicationWorld):
        raise TypeError('Experimental checkpoints require CommunicationWorld provenance/configuration')
    world.validate()
    encoded = json.dumps(world.state(), sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    with closing(sqlite3.connect(Path(path))) as db:
        db.execute('PRAGMA synchronous=FULL')
        names = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if names and names != {'communication_checkpoint'}:
            raise ValueError('Refusing to overwrite a standard or unrelated database')
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS communication_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL, sha256 TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO communication_checkpoint VALUES (1,?,?)', (encoded, digest))
    return digest


def load_experiment(path):
    """Read-only input; incomplete or modified snapshots fail instead of reseeding."""
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    with closing(sqlite3.connect(uri, uri=True)) as db:
        rows = db.execute('SELECT state,sha256 FROM communication_checkpoint WHERE id=1').fetchall()
    if len(rows) != 1:
        raise ValueError('Incomplete experimental checkpoint')
    encoded, expected = rows[0]
    if hashlib.sha256(encoded.encode()).hexdigest() != expected:
        raise ValueError('Experimental checkpoint checksum mismatch')
    return CommunicationWorld.from_state(json.loads(encoded))
