"""Explicit recovery for a locked active gameplay session, never an archive read."""
from contextlib import closing
from pathlib import Path
import sqlite3
import os

from .game_session import session_owned,writer_owned


def recover_checkpoint(path,application_id,schema_version,reader,owner_pid=None):
    path=Path(path).expanduser().resolve()
    delegated=owner_pid is not None and os.getppid()==owner_pid and writer_owned(path)
    if not session_owned(path) and not delegated:
        raise ValueError('Checkpoint recovery requires session ownership or its delegated writer gate')
    # Inspect identity without triggering recovery of a foreign/research file.
    # mode=rw below never creates a missing database. SQLite, not application file
    # deletion, performs rollback-journal recovery before the strict reader runs.
    with path.open('rb') as source:header=source.read(100)
    if (len(header)!=100 or header[:16]!=b'SQLite format 3\x00' or
        int.from_bytes(header[68:72],'big')!=application_id or
        int.from_bytes(header[60:64],'big')!=schema_version):
        raise ValueError('Not a supported gameplay checkpoint recovery target')
    with closing(sqlite3.connect(path.as_uri()+'?mode=rw',uri=True)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN')
        return reader(db)
