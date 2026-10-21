"""Disposable, mutation-invalidated IPC history. No persistence format or engine rules.

Only normal Python attribute/container operations are instrumented. Developers who
bypass these with object.__setattr__/base dict methods must explicitly invalidate.
"""
from dataclasses import dataclass,fields
from collections import deque
from functools import lru_cache
from .chronicle_index import EventJournal,AgentJournal,ChunkIndex
import pickle
import time
import weakref
from .model import Agent,Event,Episode


class WatchedDict(dict):
    def __init__(self,items=(),notify=None):
        self.notify=notify;dict.__init__(self,((k,watch(v,notify)) for k,v in dict(items).items()))
    def changed(self):
        if self.notify:self.notify()
    def __setitem__(self,k,v):dict.__setitem__(self,k,watch(v,self.notify));self.changed()
    def __delitem__(self,k):dict.__delitem__(self,k);self.changed()
    def clear(self):dict.clear(self);self.changed()
    def pop(self,*args):v=dict.pop(self,*args);self.changed();return v
    def popitem(self):v=dict.popitem(self);self.changed();return v
    def setdefault(self,k,default=None):
        if k not in self:self[k]=default
        return self[k]
    def update(self,*args,**kw):
        for k,v in dict(*args,**kw).items():self[k]=v
    def __ior__(self,other):self.update(other);return self
    def __reduce_ex__(self,protocol):return dict,(dict(self),)


class WatchedList(list):
    def __init__(self,items=(),notify=None):self.notify=notify;list.__init__(self,(watch(v,notify) for v in items))
    def changed(self):
        if self.notify:self.notify()
    def __setitem__(self,k,v):
        list.__setitem__(self,k,[watch(x,self.notify) for x in v] if isinstance(k,slice) else watch(v,self.notify));self.changed()
    def __delitem__(self,k):list.__delitem__(self,k);self.changed()
    def append(self,v):list.append(self,watch(v,self.notify));self.changed()
    def extend(self,values):list.extend(self,[watch(v,self.notify) for v in values]);self.changed()
    def insert(self,i,v):list.insert(self,i,watch(v,self.notify));self.changed()
    def clear(self):list.clear(self);self.changed()
    def pop(self,i=-1):v=list.pop(self,i);self.changed();return v
    def remove(self,v):list.remove(self,v);self.changed()
    def reverse(self):list.reverse(self);self.changed()
    def sort(self,*args,**kw):
        try:list.sort(self,*args,**kw)
        finally:self.changed()
    def __iadd__(self,values):self.extend(values);return self
    def __imul__(self,n):list.__imul__(self,n);self.changed();return self
    def __reduce_ex__(self,protocol):return list,(list(self),)


class TrackedRecord:
    def __eq__(self,other):
        # Dataclass-generated equality otherwise rejects the instrumentation subtype.
        base=Agent if isinstance(self,Agent) else Event if isinstance(self,Event) else Episode
        if type(other) not in (base,_RECORDS[base]):return NotImplemented
        return all(getattr(self,f.name)==getattr(other,f.name) for f in fields(base))
    __hash__=None

    def __delattr__(self,key):
        notify=self.__dict__.get('_checkpoint_notify')
        if notify:notify()
        object.__delattr__(self,key)
    def __setattr__(self,key,value):
        notify=self.__dict__.get('_checkpoint_notify')
        object.__setattr__(self,key,watch(value,notify) if not key.startswith('_') else value)
        if notify and not key.startswith('_'):notify()


class TrackedAgent(TrackedRecord,Agent):pass
class TrackedEvent(TrackedRecord,Event):pass
class TrackedEpisode(TrackedRecord,Episode):pass
_RECORDS={Agent:TrackedAgent,Event:TrackedEvent,Episode:TrackedEpisode}


@lru_cache(maxsize=32)
def _fields(cls):return tuple(f.name for f in fields(cls))


def watch(value,notify):
    if notify is None or type(value) in (int,str,bool,float,bytes,type(None)):return value
    if isinstance(value,(WatchedList,WatchedDict)) and value.notify is notify:return value
    if isinstance(value,dict):return WatchedDict(value,notify)
    if isinstance(value,list):return WatchedList(value,notify)
    if isinstance(value,tuple):return tuple(watch(v,notify) for v in value)
    if type(value) in _RECORDS:object.__setattr__(value,'__class__',_RECORDS[type(value)])
    if isinstance(value,TrackedRecord):
        if value.__dict__.get('_checkpoint_notify') is notify:return value
        object.__setattr__(value,'_checkpoint_notify',notify)
        for name in _fields(type(value)):
            owned=getattr(value,name)
            if type(owned) not in (int,str,bool,float,bytes,type(None)):
                object.__setattr__(value,name,watch(owned,notify))
    return value




class Block:
    @property
    def payload(self):return self._payload
    @payload.setter
    def payload(self,value):
        if value is not None and not isinstance(value,bytes):raise TypeError('Historical payload must be immutable bytes')
        self._payload=value
        if getattr(self,'on_change',None):self.on_change(self)
    def __init__(self,records):
        self.on_change=None;self.dirty=True;self.references=tuple(weakref.ref(r) for r in records);self.payload=None
        ref=weakref.ref(self)
        def notify():
            if ref() is not None:ref().invalidate()
        self.notify=notify
        for r in records:watch(r,self.notify)
    @property
    def records(self):
        records=[ref() for ref in self.references]
        if any(r is None for r in records):raise ValueError('Historical cache source is unavailable')
        return records
    def invalidate(self):
        self.dirty=True
        if self.on_change:self.on_change(self)
    def encode(self):
        if self.dirty:
            from .terrain_checkpoint import _record_vars
            records=[]
            for r in self.records:
                data=dict(_record_vars(r))
                if isinstance(r,Agent):data['memories']=[_record_vars(m) for m in r.memories]
                records.append(data)
            self.payload=pickle.dumps(records,protocol=5);self.dirty=False
        return self.payload


def restore_segmented(graph,events,dead,order):
    from .terrain_checkpoint import _restore_graph
    graph['events']=[r for block in events for r in pickle.loads(block)]+graph['events']
    agents={}
    for identity,payload in dead:agents[identity]=pickle.loads(payload)[0]
    agents.update(graph['agents']);graph['agents']={i:agents[i] for i in order}
    return _restore_graph(graph)


@dataclass(frozen=True)
class PreparedPayload:
    hot: bytes
    events: tuple = ()
    dead: tuple = ()
    order: tuple = ()
    full: bytes | None = None

    def restore(self):
        if self.full is not None:return pickle.loads(self.full)
        return restore_segmented(pickle.loads(self.hot),self.events,self.dead,self.order)


def restore_payload(payload):return payload.restore()


class SegmentedSnapshot:
    def __init__(self,payload):self.payload=payload
    def __reduce__(self):return restore_payload,(self.payload,)


class Chronicle:
    """Incremental history preparation; immutable copy-on-write capture metadata.

    Journals observe normal container edits. Bypassing a journal through retained
    aliases or base methods requires invalidate(). No persistent state is added.
    """
    def __init__(self):self.world=None;self.last_tick=-1;self.reset()
    def reset(self):
        self.blocks=[];self.dead={};self.prepared=0;self.dead_queue=deque();self.queued=set()
        self.last_living=set();self.revision=None;self.journal=None;self.agent_journal=None
        self.event_bytes=ChunkIndex();self.dead_bytes=ChunkIndex();self.dead_slots={}
        self.order=ChunkIndex();self.hot_ids=set();self.dirty=set()
    def invalidate(self):self.reset()
    def _queue(self,identity):
        if identity not in self.queued:self.dead_queue.append(identity);self.queued.add(identity)
    def _drop_dead(self,identity):
        block=self.dead.pop(identity,None)
        if block is not None:self.dirty.discard(block)
        if identity in self.dead_slots:self.dead_bytes.set(self.dead_slots[identity],None)
    def _changed(self,block):
        if block.dirty:self.dirty.add(block)
        else:self._publish(block)
    def _publish(self,block):
        value=block.payload if block.kind=='events' else (block.identity,block.payload)
        (self.event_bytes if block.kind=='events' else self.dead_bytes).set(block.slot,value)
        self.dirty.discard(block)
    def _register(self,block,kind,identity=None):
        block.kind=kind;block.identity=identity
        if kind=='events':block.slot=self.event_bytes.append(block.payload)
        else:
            if identity not in self.dead_slots:self.dead_slots[identity]=self.dead_bytes.append(None)
            block.slot=self.dead_slots[identity];self.dead_bytes.set(block.slot,(identity,block.payload))
        ref=weakref.ref(self)
        def changed(block):
            if ref() is not None:ref()._changed(block)
        block.on_change=changed
    def bind(self,w):
        if self.world is not w or w.tick<self.last_tick:self.reset();self.world=w
        self.last_tick=w.tick
        if not isinstance(w.events,EventJournal):w.events=EventJournal(w.events)
        if not isinstance(w.agents,AgentJournal):w.agents=AgentJournal(w.agents)
        # One preparation lease owns notifications for both adopted containers.
        for journal in (w.events,w.agents):
            previous=journal.owner() if journal.owner is not None else None
            if previous is not None and previous is not self:previous.invalidate();self.reset()
            journal.owner=weakref.ref(self)
        if w.events is not self.journal or self.revision!=w.events.revision or self.prepared>len(w.events):
            self.dirty={b for b in self.dirty if b.kind!='events'}
            self.blocks=[];self.prepared=0;self.event_bytes=ChunkIndex()
            self.journal=w.events;self.revision=w.events.revision
        if w.agents is not self.agent_journal or w.agents.structural:
            self.dirty={b for b in self.dirty if b.kind!='dead'}
            self.dead={};self.dead_bytes=ChunkIndex();self.dead_slots={}
            self.order=ChunkIndex(w.agents);self.dead_queue=deque(w.agents);self.queued=set(w.agents)
            self.hot_ids=set(w._living_agents);self.last_living=set()
            self.agent_journal=w.agents;w.agents.structural=False
            w.agents.changed.clear();w.agents.added.clear()
        else:
            for identity in w.agents.added:self.order.append(identity)
            for identity in sorted(w.agents.changed):
                self._drop_dead(identity);self.hot_ids.add(identity);self._queue(identity)
            w.agents.changed.clear();w.agents.added.clear()
        living=set(w._living_agents);self.hot_ids.update(living)
        for identity in sorted(self.last_living-living):self._queue(identity)
        self.last_living=living
    def _refresh(self,block,w):
        if block.kind=='dead':
            a=w.agents.get(block.identity)
            if a is None or a is not block.references[0]() or a.alive:
                self._drop_dead(block.identity)
                if a is not None:self.hot_ids.add(a.id);self._queue(a.id)
                return
        block.encode();self._publish(block)
    def prepare(self,w,budget=.004):
        # Leave room for one noninterruptible block/record unit. This is a
        # cooperative budget, not an OS/GC hard real-time deadline.
        start=time.perf_counter();self.bind(w);end=start+budget-min(.001,max(0,budget)*.5)
        while time.perf_counter()<end:
            if self.dirty:
                self._refresh(next(iter(self.dirty)),w);continue
            work=False
            if len(w.events)-self.prepared>=128:
                b=Block(w.events[self.prepared:self.prepared+128]);b.encode()
                self._register(b,'events');self.blocks.append(b);self.prepared+=128;work=True
            for _ in range(4):
                if not self.dead_queue or time.perf_counter()>=end:break
                identity=self.dead_queue.popleft();self.queued.discard(identity);a=w.agents.get(identity)
                if a is not None and not a.alive:
                    b=Block([a]);b.encode();self._register(b,'dead',identity);self.dead[identity]=b
                    self.hot_ids.discard(identity)
                elif a is not None:self.hot_ids.add(identity)
                work=True
            if not work:break
        return time.perf_counter()-start
    def detach(self,w):
        from .terrain_game import TerrainWorld
        if type(w) is not TerrainWorld:raise ValueError('Chronicle requires TerrainWorld')
        self.bind(w)
        for block in tuple(self.dirty):self._refresh(block,w)
        if not self.blocks and not self.dead:
            from .terrain_checkpoint import capture_snapshot
            return PreparedPayload(b'',full=capture_snapshot(w))
        graph=vars(w).copy();graph.pop('_living_agents')
        graph['rng']=w.rng.getstate();graph['cells']=[[vars(c) for c in row] for row in w.cells]
        graph['interventions']=[vars(p) for p in w.interventions]
        from .terrain_checkpoint import _record_vars
        graph['events']=[_record_vars(e) for e in w.events[self.prepared:]]
        graph['agents']={}
        # Pending identities are few after warming; no census of retained dead.
        for identity in self.hot_ids | self.queued:
            a=w.agents.get(identity)
            if a is not None:graph['agents'][identity]={**_record_vars(a),'memories':[_record_vars(m) for m in a.memories]}
        return PreparedPayload(pickle.dumps(graph,protocol=5),self.event_bytes.freeze(),self.dead_bytes.freeze(),self.order.freeze())
    def prepared_for(self,w):
        """Owner-loop gate, not a promise that direct cold capture is cheap."""
        return (self.world is w and w.tick>=self.last_tick and self.journal is w.events and self.agent_journal is w.agents
                and self.revision==w.events.revision and not self.dirty and not self.dead_queue
                and not w.agents.changed and not w.agents.structural
                and len(w.events)-self.prepared<128)
    def capture(self,w):
        return pickle.dumps(SegmentedSnapshot(self.detach(w)),protocol=5)
