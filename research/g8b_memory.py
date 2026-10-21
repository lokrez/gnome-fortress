"""Observation-buffer value bounds and world-lifetime isolation, without saving."""
from collections import deque
import gc,json,pickle,resource,sys,weakref
from pathlib import Path
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.decision_observation import DecisionObservation


def value_size(value,seen=None):
    seen=set() if seen is None else seen
    if id(value) in seen:return 0
    seen.add(id(value));size=sys.getsizeof(value)
    if isinstance(value,dict):return size+sum(value_size(k,seen)+value_size(v,seen) for k,v in value.items())
    if isinstance(value,(list,tuple,deque)):return size+sum(value_size(v,seen) for v in value)
    assert value is None or isinstance(value,(str,int,bool,float)),type(value)
    return size


def main():
    rows=[]
    for tick in (0,3000,10000,26000):
        w=TerrainWorld(1) if tick==0 else pickle.loads(Path(f'/tmp/gnome-g8a2-generated-fixtures/{tick}.pickle').read_bytes())
        o=DecisionObservation();o.start(w,min(w.living(),key=lambda a:(a.age,a.id)).id);w.step(180)
        size=value_size(o.records);count=len(o.records);ref=weakref.ref(w)
        del w;gc.collect();assert ref() is None
        rows.append(dict(start_tick=tick,records=count,heap_bytes=size,world_released=True,
                         cumulative_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
    Path('docs/g8b/evidence/memory.json').write_text(json.dumps(rows,indent=2)+'\n')


if __name__=='__main__':main()
