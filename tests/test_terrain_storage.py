import copy
import sqlite3

import pytest
from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import save_game as save_legacy,load_game as load_legacy,RESEARCH
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game,create_game,import_legacy,APPLICATION_ID


def test_new_exact_save_rng_and_reference(tmp_path):
    a=TerrainWorld(7);b=GameWorld(7);c=World(7)
    for tick in (0,1,10,150):
        for w in (a,b,c):w.step(tick-w.tick)
        a.validate();assert World.state(a)==World.state(b)==c.state()
    a.request('rain',1,1);a.request('drought',2,2);a.step(5)
    p=tmp_path/'fresh.g5.sqlite';create_game(a,p)
    loaded=load_game(p);assert loaded.state()==a.state()
    a.step(30);loaded.step(30);assert a.state()==loaded.state()
    with pytest.raises(FileExistsError):create_game(a,p)


def test_copy_import_exact_old_reader_and_continuation(tmp_path):
    a=GameWorld(1);a.step(9);a.request('rain',1,1);a.request('drought',2,2,1,2);a.step(5)
    src=tmp_path/'old.g1.sqlite';dst=tmp_path/'new.g5.sqlite';save_legacy(a,src);raw=src.read_bytes()
    b=import_legacy(src,dst)
    assert raw==src.read_bytes() and load_legacy(src).state()==a.state()
    assert World.state(a)==World.state(b) and b.origin['digest']==a.digest()
    for w in (a,b):w.step(60);w.validate()
    assert World.state(a)==World.state(b)
    assert load_game(dst).origin['kind']=='legacy-import'
    with pytest.raises(FileExistsError):import_legacy(src,dst)
    assert src.read_bytes()==raw
    with pytest.raises(ValueError):load_legacy(dst)
    with pytest.raises(ValueError):load_game(src)


def test_corruption_versions_interrupted_and_protection(tmp_path):
    w=TerrainWorld();p=tmp_path/'world.g5.sqlite';save_game(w,p);before=w.state()
    with sqlite3.connect(p) as db:
        db.execute("CREATE TRIGGER abort_save BEFORE UPDATE ON game_checkpoint BEGIN SELECT RAISE(ABORT,'interrupted'); END")
    w.step()
    with pytest.raises(sqlite3.IntegrityError):save_game(w,p)
    assert load_game(p).state()==before
    with sqlite3.connect(p) as db:db.execute('DROP TRIGGER abort_save');db.execute('PRAGMA user_version=77')
    raw=p.read_bytes()
    with pytest.raises(ValueError):load_game(p)
    with pytest.raises(ValueError):save_game(w,p)
    assert raw==p.read_bytes()
    with pytest.raises(ValueError):save_game(w,RESEARCH/'bad.g5.sqlite')
    with pytest.raises(ValueError):save_game(w,tmp_path/'bad.g1.sqlite')
    archive=tmp_path/'research.g5.sqlite'
    from gnome_fortress.storage import save
    save(World(),archive);raw=archive.read_bytes()
    with pytest.raises(ValueError):save_game(w,archive)
    assert raw==archive.read_bytes()
    broken=tmp_path/'broken.g5.sqlite';broken.write_bytes(b'bad')
    with pytest.raises(sqlite3.DatabaseError):load_game(broken)
    assert broken.read_bytes()==b'bad'
    data=copy.deepcopy(w.state());data['game']['record_version']=999
    with pytest.raises(ValueError):TerrainWorld.from_state(data)


def test_checksum_incomplete_and_publication_race(tmp_path,monkeypatch):
    import os
    w=TerrainWorld();p=tmp_path/'new.g5.sqlite';save_game(w,p)
    with sqlite3.connect(p) as db:db.execute("UPDATE game_checkpoint SET sha256='bad'")
    with pytest.raises(ValueError):load_game(p)
    partial=tmp_path/'partial.g5.sqlite'
    with sqlite3.connect(partial) as db:
        db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=1')
        db.execute('CREATE TABLE game_checkpoint (id,format,payload,sha256)')
    with pytest.raises(ValueError):load_game(partial)
    target=tmp_path/'race.g5.sqlite';real_link=os.link
    def raced(source,destination):
        target.write_bytes(b'another owner');real_link(source,destination)
    monkeypatch.setattr(os,'link',raced)
    with pytest.raises(FileExistsError):create_game(w,target)
    assert target.read_bytes()==b'another owner' and not list(tmp_path.glob('.g5-*'))


def test_reject_legacy_world_before_writing_any_g5_file(tmp_path):
    path=tmp_path/'wrong.g5.sqlite'
    for write in (create_game,save_game):
        with pytest.raises(ValueError,match='TerrainWorld'):write(GameWorld(),path)
        assert not path.exists()
    save_game(TerrainWorld(),path);raw=path.read_bytes()
    with pytest.raises(ValueError,match='TerrainWorld'):save_game(GameWorld(),path)
    assert path.read_bytes()==raw


@pytest.mark.parametrize('mutation',[
    lambda d:d.update(version=True),
    lambda d:d['game'].update(record_version=True),
    lambda d:d['game']['interventions'][0].update(completed_tick=True),
    lambda d:d['game']['interventions'][0]['parameters'].update(record_version=True),
    lambda d:d['game']['interventions'][0]['changes'][0].update(after_food=False),
])
def test_reject_boolean_metadata_and_transitions(mutation):
    w=TerrainWorld();w.request('rupture',2,2);w.step();data=copy.deepcopy(w.state());mutation(data)
    with pytest.raises((ValueError,AssertionError)):TerrainWorld.from_state(data)
