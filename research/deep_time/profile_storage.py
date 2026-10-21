"""Actual save path phase timing; writes ONLY private /tmp benchmark targets."""
import argparse,json,os,pickle,resource,tempfile,time,subprocess,types
from pathlib import Path
from contextlib import contextmanager
from gnome_fortress import terrain_storage as storage
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_checkpoint import capture_snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument('--scale',required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path('/tmp/gnome-deep-time'))
    p.add_argument('--reference',action='store_true',help='Use accepted 72a1017 storage source')
    a=p.parse_args()
    global storage
    if a.reference:
        source=subprocess.check_output(['git','show','72a101727d84a65dd49186503eea765825fa0987:gnome_fortress/terrain_storage.py'])
        storage=types.ModuleType('gnome_fortress._deep_time_reference')
        storage.__package__='gnome_fortress';exec(compile(source,'<accepted storage>','exec'),storage.__dict__)
    root=a.root.resolve();root.mkdir(exist_ok=True);metrics={};calls={}
    def wrap(obj,name,label):
        original=getattr(obj,name)
        def measured(*args,**kwargs):
            wall=time.perf_counter();cpu=time.process_time()
            try:return original(*args,**kwargs)
            finally:
                metrics[label]=metrics.get(label,0)+time.perf_counter()-wall
                metrics[label+'_cpu']=metrics.get(label+'_cpu',0)+time.process_time()-cpu
                calls[label]=calls.get(label,0)+1
        setattr(obj,name,measured)
    wrap(storage,'_read','strict_previous_decode')
    wrap(storage.json,'loads','json_parse');wrap(storage.json,'dumps','json_encode')
    wrap(TerrainWorld,'state','canonical_state_copy');wrap(TerrainWorld,'validate','world_validate')
    if hasattr(storage,'canonical_payload'):wrap(storage,'canonical_payload','canonical_projection_and_encoding')
    original_connect=storage.sqlite3.connect
    class TimedConnection(storage.sqlite3.Connection):
        def execute(self,sql,*args,**kw):
            label='sqlite_transaction_acquire' if sql.startswith('BEGIN IMMEDIATE') else 'sqlite_payload_write' if sql.startswith('INSERT INTO game_checkpoint') else None
            if label is None:return super().execute(sql,*args,**kw)
            t=time.perf_counter()
            try:return super().execute(sql,*args,**kw)
            finally:metrics[label]=metrics.get(label,0)+time.perf_counter()-t
        def commit(self):
            t=time.perf_counter()
            try:return super().commit()
            finally:metrics['sqlite_commit']=metrics.get('sqlite_commit',0)+time.perf_counter()-t
    def connect(*args,**kw):kw['factory']=TimedConnection;return original_connect(*args,**kw)
    storage.sqlite3.connect=connect
    t=time.perf_counter()
    if a.scale=='player':
        path=root/'player-copy.g5.sqlite';assert path.exists() and path.resolve().is_relative_to(root)
        w=storage.load_game(path)
    else:
        tick=int(a.scale)
        w=TerrainWorld(1) if tick==0 else pickle.loads(Path(f'/tmp/gnome-g8a2-generated-fixtures/{tick}.pickle').read_bytes())
        path=root/f'fixture-{tick}.g5.sqlite'
        if not path.exists():storage.create_game(w,path)
    load_seconds=time.perf_counter()-t;load_metrics=metrics.copy();metrics.clear();calls.clear()
    print('loaded',a.scale,w.tick,len(w.agents),len(w.events),'seconds',load_seconds,flush=True)
    start=time.perf_counter();storage.save_game(w,path);save_seconds=time.perf_counter()-start
    result=dict(scale=a.scale,tick=w.tick,agents=len(w.agents),events=len(w.events),load_seconds=load_seconds,
        load_phases=load_metrics,save_seconds=save_seconds,save_phases=metrics.copy(),calls=calls.copy(),
        file_bytes=path.stat().st_size,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        minor_faults=resource.getrusage(resource.RUSAGE_SELF).ru_minflt,major_faults=resource.getrusage(resource.RUSAGE_SELF).ru_majflt)
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
