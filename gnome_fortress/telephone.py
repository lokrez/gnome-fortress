"""Opt-in Phase 4B channel. Phase 3 and Phase 4A implementations are untouched."""
from collections import Counter, deque
from contextlib import closing
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3

from .communication import CommunicationWorld, origin_record
from .engine import World
from .model import Episode

MAX_PATH = 8
AUDIT_LIMIT = 128
CONDITIONS = ('individual', 'direct', 'multihop', 'masked')


@dataclass(frozen=True)
class TelephoneConfig:
    condition: str = 'individual'

    def __post_init__(self):
        if self.condition not in CONDITIONS:
            raise ValueError('Unknown telephone condition')


class TelephoneWorld(CommunicationWorld):
    implementation = 'phase4b-world-v1'

    def __init__(self, seed=1, config=TelephoneConfig()):
        self.proofs = {}
        self.audit = deque(maxlen=AUDIT_LIMIT)
        self.latest_moves = {}
        self.contact_attempts = self.meaningful_messages = self.knowledge_eligible = 0
        self.rejections = Counter()
        self.protocol = None
        super().__init__(seed, config)

    def remember(self, agent, action, feature, reward):
        key = f'{action}:{feature}'
        previous = agent.learned.get(key, 0)
        super().remember(agent, action, feature, reward)
        if key == 'move:hazard':
            origin = self.origins[agent.id][key]
            root = dict(agent=agent.id, tick=self.tick, experience=origin['firsthand_count'],
                        key=key, reward=reward, previous=previous, value=agent.learned[key],
                        xy=[agent.x, agent.y], prior_social=origin['social_count'] > 0)
            self.proofs.setdefault(agent.id, {})[key] = dict(
                root=root, path=[agent.id], key=key, masked=False, receipts=[])

    def move(self, agent):
        before = dict(tick=self.tick, actor=agent.id, start=[agent.x, agent.y],
                      learned=dict(agent.learned),
                      knowledge_before=copy.deepcopy(self.proofs.get(agent.id, {})),
                      firsthand_hazard_before=self.origins.get(agent.id, {}).get('move:hazard', {}).get('firsthand_count', 0),
                      proof_path=copy.deepcopy(self.proofs.get(agent.id, {}).get('move:hazard', {}).get('path')),
                      scheduled=agent.id in self.slots)
        super().move(agent)  # no score, ordering, movement or RNG changes
        before.update(destination=[agent.x, agent.y], terrain=self.cell(agent.x, agent.y).terrain,
                      action=agent.action, health_after=agent.health)
        self.latest_moves[agent.id] = before

    def _content(self, sender, proof):
        """No mutation/jitter. A research-only subclass supplies irrelevant content."""
        return proof['key'], sender.learned.get(proof['key'], 0), None

    def _reject(self, reason, sender, recipient):
        self.rejections[reason] += 1
        self.audit.append(dict(sequence=self.contact_attempts, tick=self.tick,
                               sender=getattr(sender, 'id', None), recipient=getattr(recipient, 'id', None),
                               status='rejected', reason=reason))
        return False

    def contact(self, sender, recipient):
        self.contact_attempts += 1
        reject = lambda reason: self._reject(reason, sender, recipient)
        if sender is None or self.agents.get(getattr(sender, 'id', None)) is not sender:
            return reject('missing_sender')
        if recipient is None or self.agents.get(getattr(recipient, 'id', None)) is not recipient:
            return reject('missing_recipient')
        if not sender.alive or not recipient.alive:
            return reject('dead')
        if sender.sleep_until > self.tick or recipient.sleep_until > self.tick:
            return reject('asleep')
        if sender.id == recipient.id or abs(sender.x-recipient.x)+abs(sender.y-recipient.y) > 1:
            return reject('nonlocal')
        self.opportunities += 1  # physical/awake opportunity, independent of content
        if self.config.condition == 'individual':
            return reject('disabled')
        proof = self.proofs.get(sender.id, {}).get('move:hazard')
        if not proof:
            return reject('no_source')
        if any(identity not in self.agents for identity in proof['path']):
            return reject('missing_source')
        if self.config.condition == 'direct' and len(proof['path']) != 1:
            return reject('forwarding_disabled')
        if recipient.id in proof['path']:
            return reject('loop')
        if len(proof['path']) >= MAX_PATH:
            return reject('hop_limit')
        key, value, intervention = self._content(sender, proof)
        masked = self.config.condition == 'masked'
        if not masked and (proof['masked'] or value >= 0):
            return reject('no_negative_content')
        if self.origins.get(recipient.id, {}).get(key, {}).get('firsthand_count', 0):
            return reject('firsthand_recipient')
        records = self.proofs.get(recipient.id, {})
        if any(record['root'] == proof['root'] for record in records.values()):
            return reject('duplicate_root')
        if key in records:
            return reject('known_association')  # no root mixing or reinforcement
        self.knowledge_eligible += 1
        old = recipient.learned.get(key, 0)
        transmitted = None if masked else value // 2
        updated = None if masked else max(-100, min(100, (3*old + transmitted)//4))
        receipt = dict(sender=sender.id, recipient=recipient.id, tick=self.tick,
                       sender_xy=[sender.x, sender.y], recipient_xy=[recipient.x, recipient.y],
                       firsthand_before=0, key=key, source_value=None if masked else value,
                       transmitted=transmitted, before=None if masked else old, after=updated,
                       intervention=intervention)
        acquired = copy.deepcopy(proof)
        acquired.update(path=proof['path'] + [recipient.id], key=key, masked=masked,
                        receipts=proof['receipts'] + [receipt])
        self.proofs.setdefault(recipient.id, {})[key] = acquired
        if not masked:
            recipient.learned[key] = updated
            origin = self.origins.setdefault(recipient.id, {}).setdefault(key, origin_record())
            origin.update(social_count=origin['social_count']+1, last_social_tick=self.tick,
                          last_source=sender.id)
            self.meaningful_messages += 1
        recipient.memories.append(Episode(self.tick, 'hear', recipient.x, recipient.y,
                                          'masked' if masked else key.split(':')[1], transmitted or 0))
        del recipient.memories[:-64]
        self.messages += 1
        self.audit.append(dict(sequence=self.contact_attempts, tick=self.tick, status='delivered',
                               sender=sender.id, recipient=recipient.id, masked=masked,
                               path=list(acquired['path']), receipt=copy.deepcopy(receipt)))
        return True

    def state(self):
        data = super().state()
        data['telephone'] = copy.deepcopy(dict(
            version=1, implementation=self.implementation, protocol=self.protocol,
            proofs=self.proofs, audit=list(self.audit), latest_moves=self.latest_moves,
            contact_attempts=self.contact_attempts, meaningful_messages=self.meaningful_messages,
            knowledge_eligible=self.knowledge_eligible, rejections=dict(self.rejections)))
        return data

    @classmethod
    def from_state(cls, data):
        extra = copy.deepcopy(data['telephone'])
        if extra['version'] != 1 or extra['implementation'] != cls.implementation:
            raise ValueError('Use the matching explicit telephone/harness loader')
        w = World.from_state.__func__(cls, copy.deepcopy(data))
        comm = data['communication']
        w.config = TelephoneConfig(**comm['config'])
        w.origins = {int(k): copy.deepcopy(v) for k, v in comm['origins'].items()}
        for field in ('opportunities', 'messages', 'decision_count'):
            setattr(w, field, comm[field])
        w.hook_seconds = 0.0
        for field in ('contact_attempts', 'meaningful_messages', 'knowledge_eligible', 'protocol'):
            setattr(w, field, extra[field])
        w.proofs = {int(k): v for k, v in extra['proofs'].items()}
        w.latest_moves = {int(k): v for k, v in extra['latest_moves'].items()}
        if len(extra['audit']) > AUDIT_LIMIT:
            raise ValueError('Oversized telephone history')
        w.audit = deque(extra['audit'], maxlen=AUDIT_LIMIT)
        w.rejections = Counter(extra['rejections'])
        w.validate()
        return w

    def validate(self):
        super().validate()
        hazard_evidence = {(e.actor, e.tick, e.detail['damage'], e.detail['x'], e.detail['y'])
                           for e in self.events if e.kind == 'hazard'}
        if len(self.audit) > AUDIT_LIMIT or set(self.latest_moves)-self.agents.keys():
            raise ValueError('Invalid bounded telephone history')
        proof_sets = list(self.proofs.items()) + [(identity, move.get('knowledge_before', {}))
                                                  for identity, move in self.latest_moves.items()]
        for owner, records in proof_sets:
            if owner not in self.agents or len(records) > 2:
                raise ValueError('Invalid proof owner/count')
            for key, proof in records.items():
                root, path, receipts = proof['root'], proof['path'], proof['receipts']
                if (not 1 <= len(path) <= MAX_PATH or len(set(path)) != len(path)
                        or path[0] != root['agent'] or path[-1] != owner
                        or any(identity not in self.agents for identity in path)
                        or len(receipts) != len(path)-1 or key != proof['key']
                        or key != (receipts[-1]['key'] if receipts else root['key'])):
                    raise ValueError('Invalid/missing/circular source path')
                if (root['key'] != 'move:hazard' or root['reward'] >= 0 or root['reward'] % 3
                        or not 1 <= root['experience'] <= self.origins.get(root['agent'], {}).get('move:hazard', {}).get('firsthand_count', 0)
                        or root['value'] != max(-100, min(100, (3*root['previous']+root['reward'])//4))
                        or (root['agent'], root['tick'], -root['reward']//3, *root['xy']) not in hazard_evidence):
                    raise ValueError('Missing/invalid physical grounding evidence')
                prior_value = root['value']
                prior_tick = root['tick']
                for index, receipt in enumerate(receipts):
                    positions = (receipt['sender_xy'], receipt['recipient_xy'])
                    if any(len(xy) != 2 or not (0 <= xy[0] < self.width and 0 <= xy[1] < self.height) for xy in positions):
                        raise ValueError('Invalid receipt coordinates')
                    if (receipt['sender'] != path[index] or receipt['recipient'] != path[index+1]
                            or receipt['firsthand_before'] != 0 or not prior_tick <= receipt['tick'] <= self.tick
                            or sum(abs(a-b) for a,b in zip(receipt['sender_xy'], receipt['recipient_xy'])) > 1):
                        raise ValueError('Invalid temporal/spatial receipt')
                    if proof['masked']:
                        if any(receipt[k] is not None for k in ('source_value','transmitted','before','after')):
                            raise ValueError('Masked receipt contains decision content')
                    else:
                        if (receipt['source_value'] != prior_value
                                or receipt['transmitted'] != prior_value//2
                                or receipt['after'] != max(-100,min(100,(3*receipt['before']+receipt['transmitted'])//4))):
                            raise ValueError('Invalid attenuation receipt')
                    if receipt['key'] == 'move:hazard' and receipt['intervention'] is not None:
                        raise ValueError('Unexpected content intervention')
                    if receipt['key'] != 'move:hazard' and not (
                            self.protocol and self.protocol.get('condition') == 'irrelevant'
                            and receipt['key'] == 'move:grass' and receipt['intervention'] == 'irrelevant-key'):
                        raise ValueError('Unexpected association key change')
                    prior_value, prior_tick = receipt['after'], receipt['tick']


def save_telephone(world, path):
    if not isinstance(world, TelephoneWorld):
        raise TypeError('Telephone checkpoints require TelephoneWorld')
    world.validate()
    encoded = json.dumps(world.state(), sort_keys=True, separators=(',', ':'))
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    with closing(sqlite3.connect(Path(path))) as db:
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if names and names != {'telephone_checkpoint'}:
            raise ValueError('Refusing to overwrite another checkpoint format')
        db.execute('PRAGMA synchronous=FULL')
        with db:
            db.execute('CREATE TABLE IF NOT EXISTS telephone_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL, sha256 TEXT NOT NULL)')
            db.execute('INSERT OR REPLACE INTO telephone_checkpoint VALUES (1,?,?)', (encoded, digest))
    return digest


def load_telephone(path, world_type=TelephoneWorld):
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro', uri=True)) as db:
        row = db.execute('SELECT state,sha256 FROM telephone_checkpoint WHERE id=1').fetchone()
    if not row or hashlib.sha256(row[0].encode()).hexdigest() != row[1]:
        raise ValueError('Incomplete/corrupt telephone checkpoint')
    return world_type.from_state(json.loads(row[0]))
