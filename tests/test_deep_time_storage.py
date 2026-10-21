"""Persistence optimizations must preserve bytes and the strict previous reader."""
import hashlib
import json
import os
import sqlite3

import pytest

from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_encoding import canonical_payload
from gnome_fortress import terrain_storage as storage
from gnome_fortress.chronicle import Chronicle


def canonical(world):
    return json.dumps(world.state(), sort_keys=True, separators=(',', ':'))


def test_projection_exact_bytes_and_chronicle_mutations():
    w = TerrainWorld(7)
    for kind in ('rain', 'drought', 'rupture', 'rewild', 'wellspring'):
        w.request(kind, 2, 2)
    for ticks in (0, 1, 10, 200, 3000):
        w.step(ticks-w.tick)
        assert canonical_payload(w) == canonical(w)
    c = Chronicle()
    for _ in range(100): c.prepare(w, .01)
    assert canonical_payload(w) == canonical(w)
    dead = next(a for a in w.agents.values() if not a.alive)
    dead.memories[0].reward -= 1
    dead.relationships.update({2: 11, 10: -4, 1: 8})
    w.events[0].detail['deep_time_unicode'] = 'moss \u2602'
    assert canonical_payload(w) == canonical(w)


def test_extended_state_preserved():
    class Extended(TerrainWorld):
        def state(self): return {**super().state(), 'extra': 'kept'}
    assert canonical_payload(Extended()) == canonical(Extended())


def test_single_strict_validation_per_overwrite(tmp_path, monkeypatch):
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'; storage.save_game(w, p)
    calls = []
    old = storage._read
    def read(db):
        calls.append(db.in_transaction)
        return old(db)
    monkeypatch.setattr(storage, '_read', read)
    w.step(); storage.save_game(w, p)
    assert calls == [True]
    assert storage.load_game(p).state() == w.state()


def test_semantically_invalid_previous_valid_sha_refused(tmp_path):
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'; storage.save_game(w, p)
    data = w.state(); data['agents'][0]['parents'] = [999999]
    payload = json.dumps(data, sort_keys=True, separators=(',', ':'))
    with sqlite3.connect(p) as db:
        db.execute('UPDATE game_checkpoint SET payload=?,sha256=?',
                   (payload, hashlib.sha256(payload.encode()).hexdigest()))
    before = p.read_bytes()
    with pytest.raises((ValueError, AssertionError)): storage.save_game(w, p)
    assert before == p.read_bytes()


def test_metadata_and_inode_change_fail_closed(tmp_path, monkeypatch):
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'; other = tmp_path/'other.g5.sqlite'
    storage.save_game(w, p); storage.save_game(TerrainWorld(42), other)
    previous = storage._write
    def replace(*args, **kwargs):
        os.replace(other, p)
        return previous(*args, **kwargs)
    monkeypatch.setattr(storage, '_write', replace)
    replacement = other.read_bytes()
    with pytest.raises(ValueError, match='changed|replaced'): storage.save_game(w, p)
    assert p.read_bytes() == replacement


def test_missing_after_preflight_not_recreated(tmp_path, monkeypatch):
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'; storage.save_game(w, p)
    previous = storage._write
    def remove(*args, **kwargs):
        p.unlink()
        return previous(*args, **kwargs)
    monkeypatch.setattr(storage, '_write', remove)
    with pytest.raises((OSError, ValueError, sqlite3.Error)): storage.save_game(w, p)
    assert not p.exists()


def test_preflight_metadata_change_does_not_overwrite(tmp_path, monkeypatch):
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'; storage.save_game(w, p)
    previous = storage._write
    altered = []
    def change(*args, **kwargs):
        with sqlite3.connect(p) as db:
            db.execute("UPDATE game_checkpoint SET sha256=?", ('0'*64,))
        altered.append(p.read_bytes())
        return previous(*args, **kwargs)
    monkeypatch.setattr(storage, '_write', change)
    with pytest.raises(ValueError, match='metadata changed'): storage.save_game(w, p)
    assert p.read_bytes() == altered[0]


def test_accepted_reader_and_byte_contract_with_all_powers(tmp_path):
    import subprocess
    import types
    module = types.ModuleType('gnome_fortress._deep_time_reader')
    module.__package__ = 'gnome_fortress'
    source = subprocess.check_output(['git', 'show',
        '72a101727d84a65dd49186503eea765825fa0987:gnome_fortress/terrain_storage.py'])
    exec(compile(source, '<accepted checkpoint reader>', 'exec'), module.__dict__)
    w = TerrainWorld(42); p = tmp_path/'world.g5.sqlite'
    for kind in ('rain', 'drought', 'rupture', 'rewild', 'wellspring'):
        w.request(kind, 2, 2)
    for ticks in (0, 1, 20, 201):
        w.step(ticks-w.tick); storage.save_game(w, p)
        assert module.load_game(p).state() == w.state()
        with sqlite3.connect(p) as db:
            payload = db.execute('SELECT payload FROM game_checkpoint').fetchone()[0]
        assert payload == canonical(w)
    restored = module.load_game(p)
    w.step(120); restored.step(120)
    assert restored.state() == w.state()


def test_commit_digest_and_launcher_do_not_rematerialize_history(tmp_path, monkeypatch, capsys):
    import argparse
    from gnome_fortress.god_world import _launch
    w = TerrainWorld(); p = tmp_path/'world.g5.sqlite'
    expected = w.digest(); result = storage.save_game(w, p)
    assert result['digest'] == expected
    def forbidden(self): raise AssertionError('Final digest needlessly rematerialized state')
    monkeypatch.setattr(TerrainWorld, 'digest', forbidden)
    parser = argparse.ArgumentParser()
    args = argparse.Namespace(new=False, import_legacy=None, seed=1, headless=True,
                              ticks=0, checkpoint_every=300, db=p)
    from gnome_fortress.game_session import game_session
    with game_session(p):
        _launch(args, parser, p)
    output = json.loads(capsys.readouterr().out)
    assert output['digest'] == expected
    assert storage.load_game(p).tick == 0
