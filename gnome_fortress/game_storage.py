"""Transactional G1 snapshots, deliberately incompatible with research checkpoints."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from .game import FORMAT, GameWorld

APPLICATION_ID=0x474E4731
RESEARCH=Path(__file__).resolve().parents[1]/'research'


def game_path(path):
    path=Path(path).expanduser().resolve()
    if not path.name.endswith('.g1.sqlite'):
        raise ValueError('Gameplay saves require a distinct .g1.sqlite suffix')
    if path.is_relative_to(RESEARCH):
        raise ValueError('Research directories are protected from gameplay writes')
    return path


def _read(db):
    if db.execute('PRAGMA application_id').fetchone()[0]!=APPLICATION_ID:
        raise ValueError('Not a G1 gameplay database; refusing to reinterpret or replace it')
    if db.execute('PRAGMA user_version').fetchone()[0]!=1:
        raise ValueError('Unsupported gameplay schema')
    rows=db.execute('SELECT id,format,payload,sha256 FROM game_checkpoint').fetchall()
    if len(rows)!=1 or rows[0][0]!=1 or rows[0][1]!=FORMAT:
        raise ValueError('Incomplete or unsupported gameplay checkpoint')
    _,_,payload,expected=rows[0]
    if hashlib.sha256(payload.encode()).hexdigest()!=expected:
        raise ValueError('Gameplay checkpoint checksum mismatch')
    try:
        return GameWorld.from_state(json.loads(payload))
    except (KeyError,TypeError,AssertionError,json.JSONDecodeError) as error:
        raise ValueError('Invalid gameplay state') from error


def load_game(path):
    path=Path(path).expanduser().resolve()
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('BEGIN')
        return _read(db)


def save_game(world,path):
    started=time.perf_counter();path=game_path(path)
    world.validate()
    payload=json.dumps(world.state(),sort_keys=True,separators=(',',':'))
    checksum=hashlib.sha256(payload.encode()).hexdigest()
    existed=path.exists()
    if existed:load_game(path)  # Fail closed on research, corrupt or incomplete files.
    path.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        try:
            if existed:
                previous=_read(db)  # Recheck the pinned transactional snapshot.
                if world.tick<previous.tick:raise ValueError('Checkpoint tick cannot move backward')
            else:
                db.execute(f'PRAGMA application_id={APPLICATION_ID}')
                db.execute('PRAGMA user_version=1')
                db.execute('CREATE TABLE game_checkpoint (id INTEGER PRIMARY KEY CHECK(id=1), format TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL)')
            db.execute('INSERT INTO game_checkpoint VALUES (1,?,?,?) ON CONFLICT(id) DO UPDATE SET format=excluded.format,payload=excluded.payload,sha256=excluded.sha256',
                       (FORMAT,payload,checksum))
            db.commit()
        except BaseException:
            db.rollback();raise
    return dict(seconds=time.perf_counter()-started,file_bytes=path.stat().st_size,tick=world.tick)


def recover_game(path):
    """Active-session reader; explicit SQLite crash rollback, no archive mutation."""
    from .checkpoint_recovery import recover_checkpoint
    return recover_checkpoint(game_path(path),APPLICATION_ID,1,_read)
