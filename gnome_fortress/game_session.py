"""One terrain-game launcher per save path (Ubuntu advisory process lock)."""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat


class SaveInUse(ValueError):pass


@contextmanager
def game_session(path):
    path=Path(path).expanduser().resolve()
    lock=path.with_name(path.name+'.lock');lock.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(lock,os.O_RDWR|os.O_CREAT|os.O_CLOEXEC|getattr(os,'O_NOFOLLOW',0),0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):raise ValueError('Invalid game-session lock file')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            owner=os.read(fd,128).decode('ascii',errors='replace').strip()
            identity=f' (process {owner})' if owner.isdigit() else ''
            raise SaveInUse('This save is already in use'+identity+'. The other game may be running or suspended. Close it and wait for it to finish saving; do not start another copy.') from None
        os.ftruncate(fd,0);os.write(fd,str(os.getpid()).encode('ascii'))
        yield
    finally:
        # Keep the lock inode. Removing it would let racing launchers lock different
        # files. The OS releases ownership on exit/kill; stale PID text is harmless.
        os.close(fd)
