import sqlite3

import pytest

from gnome_fortress.engine import World
from gnome_fortress.storage import load, save


def test_sqlite_queryable_and_valid(tmp_path):
    path = tmp_path / "world.sqlite"
    w = World(42)
    w.step(200)
    save(w, path)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
        assert db.execute("SELECT count(*) FROM agents WHERE alive=1").fetchone()[0] == len(w.living())
        assert db.execute("SELECT count(*) FROM ancestry").fetchone()[0] == (len(w.agents)-60)*2
        assert db.execute("SELECT count(*) FROM memories").fetchone()[0] > 0
        assert db.execute("SELECT count(*) FROM relationships").fetchone()[0] > 0


def test_failed_save_rolls_back_previous_checkpoint(tmp_path):
    path = tmp_path / "world.sqlite"
    w = World()
    save(w, path)
    before = w.digest()
    with sqlite3.connect(path) as db:
        db.execute("CREATE TRIGGER fail_save BEFORE INSERT ON memories BEGIN SELECT RAISE(ABORT, 'test failure'); END")
    w.step(5)
    with pytest.raises(sqlite3.IntegrityError):
        save(w, path)
    assert load(path).digest() == before


def test_missing_checkpoint_does_not_create_file(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        load(path)
    assert not path.exists()


def test_checkpoint_connections_are_explicitly_closed(tmp_path, monkeypatch):
    closed = []
    original_connect = sqlite3.connect

    class TrackedConnection(sqlite3.Connection):
        def close(self):
            closed.append(self)
            super().close()

    def connect(*args, **kwargs):
        return original_connect(*args, factory=TrackedConnection, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", connect)
    path = tmp_path / "closed.sqlite"
    save(World(), path)
    load(path)
    assert len(closed) == 2
