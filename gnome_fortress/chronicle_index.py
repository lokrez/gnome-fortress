"""Disposable Chronicle journals and copy-on-write immutable metadata chunks."""
from collections.abc import MutableMapping,MutableSequence
from dataclasses import dataclass


class EventJournal(MutableSequence):
    """Adopt the list without an initial O(history) copy. Aliases require invalidate."""
    def __init__(self,values=()):
        self.data=values if isinstance(values,list) else list(values)
        self.revision=0;self.owner=None
    def invalidate(self):self.revision+=1
    def __len__(self):return len(self.data)
    def __iter__(self):return iter(self.data)
    def __getitem__(self,key):return self.data[key]
    def __setitem__(self,key,value):self.data[key]=value;self.invalidate()
    def __delitem__(self,key):del self.data[key];self.invalidate()
    def insert(self,key,value):self.data.insert(key,value);self.invalidate()
    def append(self,value):self.data.append(value)
    def extend(self,values):self.data.extend(values.data if isinstance(values,EventJournal) else values)
    def __iadd__(self,values):self.extend(values);return self
    def __imul__(self,n):self.data*=n;self.invalidate();return self
    def reverse(self):self.data.reverse();self.invalidate()
    def sort(self,*args,**kwargs):
        try:self.data.sort(*args,**kwargs)
        finally:self.invalidate()
    def copy(self):return self.data.copy()
    def __eq__(self,other):return self.data==(other.data if isinstance(other,EventJournal) else other)
    def __repr__(self):return repr(self.data)
    def __reduce_ex__(self,protocol):return list,(self.data,)


class AgentJournal(MutableMapping):
    """Normal mapping edits are observable; values are the actual model records."""
    def __init__(self,values):
        self.data=values;self.changed=set();self.added=[];self.structural=False;self.owner=None
    def __len__(self):return len(self.data)
    def __iter__(self):return iter(self.data)
    def __getitem__(self,key):return self.data[key]
    def __setitem__(self,key,value):
        if key not in self.data:self.added.append(key)
        self.data[key]=value;self.changed.add(key)
    def __delitem__(self,key):del self.data[key];self.structural=True
    def keys(self):return self.data.keys()
    def values(self):return self.data.values()
    def items(self):return self.data.items()
    def clear(self):self.data.clear();self.structural=True
    def copy(self):return self.data.copy()
    def popitem(self):
        value=self.data.popitem();self.structural=True;return value
    def __reversed__(self):return reversed(self.data)
    def __ior__(self,other):self.update(other);return self
    def __reduce_ex__(self,protocol):return dict,(self.data,)


@dataclass(frozen=True)
class FrozenChunks:
    chunks:tuple
    def __iter__(self):
        for chunk in self.chunks:
            for value in chunk:
                if value is not None:yield value
    def __len__(self):return sum(value is not None for chunk in self.chunks for value in chunk)


class ChunkIndex:
    def __init__(self,values=()):
        values=tuple(values);self.chunks=[values[i:i+128] for i in range(0,len(values),128)];self.size=len(values)
    def append(self,value):
        slot=self.size;self.size+=1
        if slot%128:self.chunks[-1]=self.chunks[-1]+(value,)
        else:self.chunks.append((value,))
        return slot
    def set(self,slot,value):
        chunk,offset=divmod(slot,128);old=self.chunks[chunk]
        self.chunks[chunk]=old[:offset]+(value,)+old[offset+1:]
    def freeze(self):return FrozenChunks(tuple(self.chunks))
