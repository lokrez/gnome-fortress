"""G5 identity, checksummed transactional checkpoints, explicit copy-only import."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time

from .terrain_game import FORMAT, TerrainWorld
from .game_storage import RESEARCH, load_game as load_legacy

APPLICATION_ID=0x474E4735
SCHEMA_VERSION=1


def game_path(path):
    path=Path(path).expanduser().resolve()
    if not path.name.endswith('.g5.sqlite') or path.is_relative_to(RESEARCH):
        raise ValueError('Terrain saves require .g5.sqlite outside protected research paths')
    return path


def _read(db):
    if db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID or db.execute('PRAGMA user_version').fetchone()[0]!=SCHEMA_VERSION:
        raise ValueError('Not a supported G5 terrain checkpoint')
    rows=db.execute('SELECT id,format,payload,sha256 FROM game_checkpoint').fetchall()
    if len(rows)!=1 or rows[0][0]!=1 or rows[0][1]!=FORMAT:
        raise ValueError('Incomplete/unknown terrain checkpoint')
    _,_,payload,checksum=rows[0]
    if not isinstance(payload,str) or hashlib.sha256(payload.encode()).hexdigest()!=checksum:
        raise ValueError('Terrain checkpoint checksum mismatch')
    try:return TerrainWorld.from_state(json.loads(payload))
    except (KeyError,TypeError,AssertionError,IndexError,AttributeError,json.JSONDecodeError) as error:
        raise ValueError('Invalid terrain checkpoint state') from error


def load_game(path):
    path=Path(path).expanduser().resolve()
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('BEGIN')
        return _read(db)


def _write(world,path,existing):
    payload=json.dumps(world.state(),sort_keys=True,separators=(',',':'))
    checksum=hashlib.sha256(payload.encode()).hexdigest()
    with closing(sqlite3.connect(path)) as db:
        db.execute('PRAGMA synchronous=FULL');db.execute('BEGIN IMMEDIATE')
        try:
            if existing:_read(db)
            else:
                db.execute(f'PRAGMA application_id={APPLICATION_ID}')
                db.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                db.execute('CREATE TABLE game_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1),format TEXT NOT NULL,payload TEXT NOT NULL,sha256 TEXT NOT NULL)')
            db.execute('INSERT INTO game_checkpoint VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET format=excluded.format,payload=excluded.payload,sha256=excluded.sha256',(FORMAT,payload,checksum))
            db.commit()
        except BaseException:db.rollback();raise


def create_game(world,path):
    """Publish a complete new file exclusively. No check-then-replace destination race."""
    started=time.perf_counter()
    if not isinstance(world,TerrainWorld):raise ValueError('G5 storage requires TerrainWorld')
    path=game_path(path);world.validate()
    if path.exists():raise FileExistsError('New terrain checkpoint requires an unused destination')
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.g5-',suffix='.tmp',dir=path.parent);os.close(fd)
    temporary=Path(name)
    try:
        _write(world,temporary,False)
        # Atomic exclusive publication on the same filesystem; never replaces a file.
        os.link(temporary,path)
    finally:temporary.unlink(missing_ok=True)
    return dict(seconds=time.perf_counter()-started,file_bytes=path.stat().st_size,tick=world.tick)


def save_game(world,path):
    started=time.perf_counter()
    if not isinstance(world,TerrainWorld):raise ValueError('G5 storage requires TerrainWorld')
    path=game_path(path);world.validate()
    if not path.exists():return create_game(world,path)
    load_game(path)  # Fail closed before any attempted update.
    _write(world,path,True)
    return dict(seconds=time.perf_counter()-started,file_bytes=path.stat().st_size,tick=world.tick)


def import_legacy(source,destination):
    destination=game_path(destination)
    if destination.exists():raise FileExistsError('Import destination already exists')
    world=TerrainWorld.from_legacy(load_legacy(source))
    create_game(world,destination)
    return world
