"""One gameplay launcher per save path (Ubuntu advisory process lock)."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat


_sessions={}
_writers={}


class SaveInUse(ValueError):pass


def session_owned(path):
    return _sessions.get(Path(path).expanduser().resolve())==os.getpid()


def writer_owned(path):
    return _writers.get(Path(path).expanduser().resolve())==os.getpid()


@contextmanager
def game_session(path):
    path=Path(path).expanduser().resolve()
    lock=path.with_name(path.name+'.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_CLOEXEC|getattr(os,'O_NOFOLLOW',0),0o600)
    registered=False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('Invalid game-session lock file')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            owner=os.read(fd,128).decode('ascii',errors='replace').strip()
            identity=f' (process {owner})' if owner.isdigit() else ''
            raise SaveInUse('This save is already in use'+identity+'. The other game may be running or suspended. Close it and wait for it to finish saving; do not start another copy.') from None
        os.ftruncate(fd,0);os.write(fd,str(os.getpid()).encode('ascii'))
        # A killed prior owner may still have a transaction in flight. Refuse
        # before loading until its writer releases this separate gate.
        with checkpoint_write_lock(path):pass
        _sessions[path]=os.getpid();registered=True
        yield
    finally:
        if registered:_sessions.pop(path,None)
        # Keep the lock inode. Removing it would let racing launchers lock different
        # files. The OS releases ownership on exit/kill; stale PID text is harmless.
        os.close(fd)


@contextmanager
def checkpoint_write_lock(path):
    """Single writer/drain gate; worker owns its own descriptor, never owner's."""
    path=Path(path).expanduser().resolve()
    lock=path.with_name(path.name+'.writer.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_CLOEXEC|getattr(os,'O_NOFOLLOW',0),0o600)
    registered=False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('Invalid checkpoint writer lock')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            raise SaveInUse('Checkpoint writer is still active; wait for it to finish before opening this world.') from None
        _writers[path]=os.getpid();registered=True
        yield
    finally:
        if registered:_writers.pop(path,None)
        os.close(fd)
