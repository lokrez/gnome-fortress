"""Schema-1 compatible atomic checkpoints with checked incremental history."""
from contextlib import closing
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from .engine import World
from .model import Agent,Cell,Episode,Event

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
CHECKS = 'CREATE TABLE IF NOT EXISTS record_checks (agent INTEGER PRIMARY KEY, digest TEXT NOT NULL)'
AGENT_FIELDS = tuple(f.name for f in fields(Agent) if f.name not in ('parents','memories','relationships'))


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def add_hash(digest,value):
    digest.update(encode(value).encode()); digest.update(b'\n')


def header(world):
    return dict(version=1,seed=world.seed,width=world.width,height=world.height,
                tick=world.tick,next_id=world.next_id,cursor=world.cursor,
                slots=world.slots,rng=world.rng.getstate())


def record(a,timings=None):
    # Exclude large nested records BEFORE serialization; no recursive asdict copies.
    digest=hashlib.sha256()
    def measured(name,build):
        started=time.perf_counter()
        value=build();add_hash(digest,value)
        if timings is not None:timings[name]=timings.get(name,0)+time.perf_counter()-started
        return value
    text=measured('agent_fields_seconds',lambda:encode({k:getattr(a,k) for k in AGENT_FIELDS}))
    parents=measured('ancestry_seconds',lambda:[(a.id,p,i) for i,p in enumerate(a.parents)])
    memories=measured('memory_seconds',lambda:[(a.id,i,m.tick,m.action,m.x,m.y,m.feature,m.reward) for i,m in enumerate(a.memories)])
    relations=measured('relationship_seconds',lambda:[(a.id,target,value) for target,value in sorted(a.relationships.items())])
    return text,parents,memories,relations,digest.hexdigest()


def event_rows(world):
    for i,e in enumerate(world.events):
        yield i,e.tick,e.kind,e.actor,e.target,encode(e.detail)


def signature(path):
    # A different writer, external edit, replacement, or WAL change invalidates reuse.
    values=[]
    for p in (path,Path(str(path)+'-wal'),Path(str(path)+'-journal')):
        try:
            s=p.stat(); values.append((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns))
        except FileNotFoundError: values.append(None)
    return tuple(values)


def save(world:World,path):
    """Caller must hold the world at a complete tick until this function returns.

    All current agent content and the entire event prefix are checked, including
    dead records. Only unchanged, previously verified database rows are reused.
    """
    start=time.perf_counter(); world.validate()
    metrics={'validation_seconds':time.perf_counter()-start,'agents_written':0,'events_written':0,
             'agent_serialization_seconds':0.,'agent_sql_seconds':0.}
    path=Path(path).resolve(); key=str(path)
    cached=getattr(world,'_checkpoint_cache',{}).get(key)
    before=signature(path)
    with closing(sqlite3.connect(path)) as db:
        db.execute('PRAGMA foreign_keys=ON'); db.execute('PRAGMA synchronous=FULL')
        db.executescript(SCHEMA); db.execute(CHECKS)
        db.execute('BEGIN IMMEDIATE')
        db.execute('PRAGMA defer_foreign_keys=ON')
        metadata=dict(db.execute('SELECT key,value FROM metadata'))
        if metadata and metadata.get('schema_version')!='1': raise ValueError('Unsupported checkpoint schema')
        trusted=bool(cached and cached==(before,metadata.get('revision')) and 'integrity' in metadata)
        old_checks=dict(db.execute('SELECT agent,digest FROM record_checks')) if trusted else {}
        previous=json.loads(metadata['integrity']) if trusted else {}
        count=previous.get('events',0)
        # Stream through the prefix to catch edits, truncation and divergent forks.
        t=time.perf_counter(); event_digest=hashlib.sha256(); prefix_digest=event_digest.hexdigest() if count==0 else None
        for row in event_rows(world):
            add_hash(event_digest,row)
            if row[0]+1==count:prefix_digest=event_digest.hexdigest()
        trusted=trusted and len(world.events)>=count and prefix_digest==previous.get('events_sha256')
        trusted=trusted and set(old_checks).issubset(world.agents)
        metrics['event_serialization_seconds']=time.perf_counter()-t
        revision=str(int(metadata.get('revision','0'))+1)
        try:
            if not trusted:
                for table in ('ancestry','memories','relationships','record_checks','events','agents','cells','metadata'):
                    db.execute(f'DELETE FROM {table}')
                old_checks={}; count=0
            agent_digest=hashlib.sha256()
            for a in world.agents.values():
                t=time.perf_counter(); text,parents,memories,relations,digest=record(a,metrics)
                metrics['agent_serialization_seconds']+=time.perf_counter()-t
                add_hash(agent_digest,(a.id,digest))
                if old_checks.get(a.id)==digest: continue
                t=time.perf_counter()
                for table,column in (('ancestry','child'),('memories','agent'),('relationships','source')):
                    db.execute(f'DELETE FROM {table} WHERE {column}=?',(a.id,))
                db.execute('''INSERT INTO agents VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,alive=excluded.alive,born=excluded.born,died=excluded.died,state=excluded.state''',
                    (a.id,a.name,int(a.alive),a.born,a.died,text))
                db.executemany('INSERT INTO ancestry VALUES (?,?,?)',parents)
                db.executemany('INSERT INTO memories VALUES (?,?,?,?,?,?,?,?)',memories)
                db.executemany('INSERT INTO relationships VALUES (?,?,?)',relations)
                db.execute('INSERT OR REPLACE INTO record_checks VALUES (?,?)',(a.id,digest))
                metrics['agents_written']+=1
                metrics['agent_sql_seconds']+=time.perf_counter()-t
            cells=[(x,y,c.terrain,c.food) for y,row in enumerate(world.cells) for x,c in enumerate(row)]
            cell_digest=hashlib.sha256(); add_hash(cell_digest,cells)
            db.executemany('INSERT OR REPLACE INTO cells VALUES (?,?,?,?)',cells)
            t=time.perf_counter()
            # Only encode/insert new events on the second pass, not the old prefix.
            def appended():
                for i in range(count,len(world.events)):
                    e=world.events[i]
                    yield i,e.tick,e.kind,e.actor,e.target,encode(e.detail)
            db.executemany('INSERT INTO events VALUES (?,?,?,?,?,?)',appended())
            metrics['events_written']=len(world.events)-count
            metrics['event_sql_seconds']=time.perf_counter()-t
            text=encode(header(world))
            integrity=dict(format=1,agents=len(world.agents),events=len(world.events),
                cells=len(cells),agents_sha256=agent_digest.hexdigest(),events_sha256=event_digest.hexdigest(),
                cells_sha256=cell_digest.hexdigest(),header_sha256=hashlib.sha256(text.encode()).hexdigest())
            db.executemany('INSERT OR REPLACE INTO metadata VALUES (?,?)',
                [('schema_version','1'),('world',text),('integrity',encode(integrity)),('revision',revision)])
            db.execute('PRAGMA user_version=2')
            db.commit()
        except BaseException:
            db.rollback(); raise
    world._checkpoint_cache={key:(signature(path),revision)}
    metrics.update(seconds=time.perf_counter()-start,incremental=bool(trusted),file_bytes=path.stat().st_size)
    return metrics


def load(path):
    path=Path(path).resolve()
    mode='rw' if Path(str(path)+'-journal').exists() else 'ro'
    uri=path.as_uri()+'?mode='+mode
    try:
        with closing(sqlite3.connect(uri,uri=True)) as db:
            db.execute('BEGIN')  # Pin one atomic read snapshot across all tables.
            user_version=db.execute('PRAGMA user_version').fetchone()[0]
            metadata=dict(db.execute('SELECT key,value FROM metadata'))
            if user_version not in (0,2): raise ValueError('Unsupported checkpoint format')
            if user_version==2 and not {'integrity','revision'}.issubset(metadata):
                raise ValueError('Missing checkpoint integrity metadata')
            if metadata['schema_version']!='1': raise ValueError('Unsupported checkpoint schema')
            data=json.loads(metadata['world'])
            data.update(agents=[],events=[],cells=[])
            w=World.from_state(data)
            w.cells=[[None]*w.width for _ in range(w.height)]
            cells=[]
            for x,y,terrain,food in db.execute('SELECT * FROM cells ORDER BY y,x'):
                if not (0<=x<w.width and 0<=y<w.height): raise ValueError('Invalid cell coordinate')
                w.cells[y][x]=Cell(terrain,food); cells.append((x,y,terrain,food))
            if len(cells)!=w.width*w.height or any(c is None for r in w.cells for c in r):
                raise ValueError('Incomplete cell grid')
            for identity,name,alive,born,died,text in db.execute('SELECT * FROM agents ORDER BY id'):
                a=Agent(parents=(),**json.loads(text))
                if (a.id,a.name,int(a.alive),a.born,a.died)!=(identity,name,alive,born,died):
                    raise ValueError('Agent column/state mismatch')
                w.agents[a.id]=a
            for child,parent,pos in db.execute('SELECT * FROM ancestry ORDER BY child,position'):
                a=w.agents[child]
                if pos!=len(a.parents): raise ValueError('Ancestry sequence gap')
                a.parents+= (parent,)
            for identity,seq,tick,action,x,y,feature,reward in db.execute('SELECT * FROM memories ORDER BY agent,sequence'):
                a=w.agents[identity]
                if seq!=len(a.memories): raise ValueError('Memory sequence gap')
                a.memories.append(Episode(tick,action,x,y,feature,reward))
            for source,target,value in db.execute('SELECT * FROM relationships ORDER BY source,target'):
                if target not in w.agents: raise ValueError('Unknown relationship target')
                w.agents[source].relationships[target]=value
            event_digest=hashlib.sha256()
            for row in db.execute('SELECT * FROM events ORDER BY sequence'):
                seq,tick,kind,actor,target,detail=row
                if seq!=len(w.events): raise ValueError('Event sequence gap')
                if any(i is not None and i not in w.agents for i in (actor,target)):
                    raise ValueError('Unknown event identity')
                w.events.append(Event(tick,kind,actor,target,json.loads(detail)))
                if 'integrity' in metadata: add_hash(event_digest,row)
            w._rebuild_index(); w.validate()
            if 'integrity' in metadata:
                expected=json.loads(metadata['integrity'])
                if expected['format']!=1: raise ValueError('Unsupported integrity format')
                checks=dict(db.execute('SELECT agent,digest FROM record_checks'))
                if len(checks)!=len(w.agents): raise ValueError('Incomplete agent checksums')
                agents_digest=hashlib.sha256()
                for a in w.agents.values():
                    digest=record(a)[-1]
                    if checks.get(a.id)!=digest: raise ValueError(f'Agent checksum mismatch: {a.id}')
                    add_hash(agents_digest,(a.id,digest))
                cell_digest=hashlib.sha256(); add_hash(cell_digest,cells)
                actual=dict(format=1,agents=len(w.agents),events=len(w.events),cells=len(cells),
                    agents_sha256=agents_digest.hexdigest(),events_sha256=event_digest.hexdigest(),
                    cells_sha256=cell_digest.hexdigest(),header_sha256=hashlib.sha256(metadata['world'].encode()).hexdigest())
                if actual!=expected: raise ValueError('Checkpoint integrity mismatch')
        if 'integrity' in metadata: w._checkpoint_cache={str(path):(signature(path),metadata['revision'])}
        return w
    except (KeyError,TypeError,IndexError,AssertionError) as error:
        raise ValueError(f'Incomplete or inconsistent checkpoint: {error}') from error
