"""Disposable, mutation-invalidated IPC history. No persistence format or engine rules.

Only normal Python attribute/container operations are instrumented. Developers who
bypass these with object.__setattr__/base dict methods must explicitly invalidate.
"""
from dataclasses import dataclass,fields
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
        for f in fields(value):object.__setattr__(value,f.name,watch(getattr(value,f.name),notify))
    return value


class EventJournal(WatchedList):
    """Appending needs no prefix invalidation; every other edit does."""
    def __init__(self,values=()):
        self.revision=0;self.owner=None;ref=weakref.ref(self)
        def notify():
            if ref() is not None:ref().invalidate()
        self.notify=notify;list.__init__(self,values)
    def invalidate(self):self.revision+=1
    def append(self,value):list.append(self,value)
    def extend(self,values):list.extend(self,values)
    def __iadd__(self,values):self.extend(values);return self


class Block:
    def __init__(self,records):
        self.dirty=True;self.references=tuple(weakref.ref(r) for r in records);self.payload=None
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
    def invalidate(self):self.dirty=True
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
    """Bounded preparations, one cached byte representation of retained history.

    Grows with canonical history, not with checkpoint generations. Full current
    mutable state and unprepared tails are always detached by the final pickle.
    """
    def __init__(self):self.world=None;self.last_tick=-1;self.reset()
    def reset(self):
        self.blocks=[];self.dead={};self.prepared=0;self.dead_queue=[];self.dead_cursor=0
        self.known_agents=0;self.known_next_id=0;self.last_living=set();self.revision=None;self.journal=None
    def invalidate(self):self.reset()
    def bind(self,w):
        if self.world is not w or w.tick<self.last_tick:
            self.reset();self.world=w
        self.last_tick=w.tick
        if w.events is not self.journal:
            self.blocks=[];self.prepared=0
            if not isinstance(w.events,EventJournal):w.events=EventJournal(w.events)
            previous=w.events.owner() if w.events.owner is not None else None
            if previous is not None and previous is not self:
                previous.invalidate();self.reset()
            w.events.owner=weakref.ref(self)
            self.journal=w.events;self.revision=w.events.revision
        if self.revision!=w.events.revision or self.prepared>len(w.events):
            self.blocks=[];self.prepared=0;self.revision=w.events.revision
        living=set(w._living_agents)
        if self.known_agents==0:
            self.dead_queue=[i for i,a in w.agents.items() if not a.alive]
            self.dead_cursor=0
        elif len(w.agents)<self.known_agents or w.next_id<self.known_next_id:
            self.dead={};self.dead_queue=[i for i,a in w.agents.items() if not a.alive];self.dead_cursor=0
        else:
            # Birth IDs are monotonic. Never rescan all deceased records on births.
            self.dead_queue.extend(i for i in range(self.known_next_id,w.next_id)
                                   if i in w.agents and not w.agents[i].alive)
        self.dead_queue.extend(sorted(self.last_living-living))
        self.known_agents=len(w.agents);self.known_next_id=w.next_id
        self.last_living=living
    def prepare(self,w,budget=.004):
        start=time.perf_counter();self.bind(w);end=start+budget
        while time.perf_counter()<end:
            work=False
            if len(w.events)-self.prepared>=128:
                b=Block(w.events[self.prepared:self.prepared+128]);b.encode();self.blocks.append(b);self.prepared+=128;work=True
            for _ in range(4):
                if self.dead_cursor>=len(self.dead_queue) or time.perf_counter()>=end:break
                identity=self.dead_queue[self.dead_cursor];self.dead_cursor+=1;a=w.agents.get(identity)
                if a is not None and not a.alive:
                    b=Block([a]);b.encode();self.dead[identity]=b
                work=True
            if not work:break
        # Drop drained queues; no per-frame growth once preparation is complete.
        if self.dead_cursor==len(self.dead_queue):self.dead_queue=[];self.dead_cursor=0
        return time.perf_counter()-start
    def detach(self,w):
        from .terrain_game import TerrainWorld
        if type(w) is not TerrainWorld:raise ValueError('Chronicle requires TerrainWorld')
        self.bind(w)
        if not self.blocks and not self.dead:
            from .terrain_checkpoint import capture_snapshot
            return PreparedPayload(b'',full=capture_snapshot(w))
        graph=vars(w).copy();graph.pop('_living_agents')
        graph['rng']=w.rng.getstate();graph['cells']=[[vars(c) for c in row] for row in w.cells]
        graph['interventions']=[vars(p) for p in w.interventions]
        # Newly appended/unprepared events and all mutable records belong to THIS tick.
        from .terrain_checkpoint import _record_vars
        graph['events']=[_record_vars(e) for e in w.events[self.prepared:]]
        graph['agents']={};dead=[]
        for i,a in w.agents.items():
            b=self.dead.get(i)
            if b is not None and b.references[0]() is a and not a.alive:dead.append((i,b.encode()))
            else:
                graph['agents'][i]={**_record_vars(a),'memories':[_record_vars(m) for m in a.memories]}
                if not a.alive and b is not None:self.dead.pop(i,None);self.dead_queue.append(i)
        return PreparedPayload(pickle.dumps(graph,protocol=5),tuple(b.encode() for b in self.blocks),tuple(dead),tuple(w.agents))

    def capture(self,w):
        # Standalone bytes API for tests/tools; production queues the immutable
        # bundle so history-byte copying occurs in the pool's feeder, not here.
        return pickle.dumps(SegmentedSnapshot(self.detach(w)),protocol=5)
