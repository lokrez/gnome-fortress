import copy
import sqlite3

import pytest

from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld
from gnome_fortress.game_storage import load_game,save_game
from gnome_fortress.storage import save
from research.phase3.reference.engine import World as Reference


@pytest.mark.parametrize('seed',[1,42])
def test_no_power_is_exact_reference(seed):
    game,standard,reference=GameWorld(seed),World(seed),Reference(seed)
    for boundary in (0,1,10,100,500):
        for w in (game,standard,reference):w.step(boundary-w.tick)
        assert World.state(game)==standard.state()==reference.state()
        game.validate()


@pytest.mark.parametrize('power,grass,forest',[('rain',8,16),('drought',0,0)])
def test_regeneration_boundaries_and_expiration(power,grass,forest):
    w=GameWorld();w.step(8)
    for row in w.cells:
        for c in row:
            if c.terrain in ('grass','forest'):c.food=0
    # Resource-only hook check: no agents can consume or move during this test.
    before=copy.deepcopy(World.state(w));rng=w.rng.getstate()
    p=w.request(power,0,0,radius=3,duration=1)
    assert w.rng.getstate()==rng and World.state(w)['agents']==before['agents']
    assert p.activation_tick==9 and p.expires_tick==10 and p.status=='queued'
    w.step();assert p.status=='active'
    old=[[c.food for c in row] for row in w.cells]
    w._regenerate_food()
    for y,row in enumerate(w.cells):
        for x,c in enumerate(row):
            base=8 if c.terrain=='forest' else 4
            inc=(forest if c.terrain=='forest' else grass) if x*x+y*y<=9 else base
            if c.terrain in ('grass','forest'):assert c.food==min(100,old[y][x]+inc)
            else:assert c.food==old[y][x]
    w.step();assert p.status=='expired' and p.expired_tick==10
    old=[[c.food for c in row] for row in w.cells];w._regenerate_food()
    assert all(c.food==min(100,old[y][x]+(8 if c.terrain=='forest' else 4))
               for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain in ('grass','forest'))


def test_overlap_repeated_requests_cap_and_drought_preserves_supplies():
    w=GameWorld();w.step(8)
    a=w.request('rain',1,1,2,50);b=w.request('rain',1,1,2,50);d=w.request('drought',1,1,0,1)
    w.step();w.cell(1,1).food=37;w.cell(2,1).food=96
    w._regenerate_food()
    assert w.cell(1,1).food==37 and w.cell(2,1).food==100
    assert b.totals['regenerated']==0 and d.totals['delta']==-4
    assert a.id==1 and b.id==2 and d.id==3
    w.step();assert d.status=='expired'


def test_replay_and_active_save_load(tmp_path):
    worlds=[GameWorld(4),GameWorld(4)]
    for w in worlds:
        w.step(9);w.request('rain',0,0,5,22);w.request('drought',2,2,2,11);w.step(5)
    path=tmp_path/'active.g1.sqlite';save_game(worlds[0],path);loaded=load_game(path)
    assert loaded.state()==worlds[0].state()
    worlds.append(loaded)
    for w in worlds:w.step(40);w.validate()
    assert worlds[0].state()==worlds[1].state()==worlds[2].state()
    assert all(p.status=='expired' for p in loaded.interventions)


def test_research_protection_corruption_and_interrupted_transaction(tmp_path):
    research=tmp_path/'archive.g1.sqlite';save(World(),research);original=research.read_bytes()
    with pytest.raises(ValueError):save_game(GameWorld(),research)
    assert research.read_bytes()==original
    with pytest.raises(ValueError):save_game(GameWorld(),tmp_path/'research.sqlite')
    from gnome_fortress.game_storage import RESEARCH
    with pytest.raises(ValueError):save_game(GameWorld(),RESEARCH/'accidental.g1.sqlite')
    p=tmp_path/'world.g1.sqlite';w=GameWorld();save_game(w,p);before=w.state()
    with sqlite3.connect(p) as db:db.execute("CREATE TRIGGER abort_save BEFORE UPDATE ON game_checkpoint BEGIN SELECT RAISE(ABORT,'interrupted'); END")
    w.step()
    with pytest.raises(sqlite3.IntegrityError):save_game(w,p)
    assert load_game(p).state()==before
    with sqlite3.connect(p) as db:db.execute('DROP TRIGGER abort_save')
    with sqlite3.connect(p) as db:db.execute("UPDATE game_checkpoint SET sha256='bad'")
    with pytest.raises(ValueError):load_game(p)
    corrupted=p.read_bytes()
    with pytest.raises(ValueError):save_game(w,p)
    assert p.read_bytes()==corrupted
    p.write_bytes(b'not sqlite')
    with pytest.raises(sqlite3.DatabaseError):load_game(p)


def test_extinction_latches_stops_and_does_not_resurrect(tmp_path):
    w=GameWorld();w.request('rain',1,1)
    for a in list(w.living()):w.kill(a,'test')
    assert w.extinct and w.extinct_tick==0
    state=w.state();w.step(100);assert w.state()==state
    with pytest.raises(ValueError):w.request('rain',1,1)
    path=tmp_path/'extinct.g1.sqlite';save_game(w,path);loaded=load_game(path);loaded.step(10)
    assert loaded.state()==state and len(loaded.agents)==60


@pytest.mark.parametrize('args',[('storm',1,1),('rain',-1,1),('rain',1,1,-1),('rain',1,1,2,0),('rain',1.1,1)])
def test_invalid_power_inputs(args):
    w=GameWorld();before=w.state()
    with pytest.raises(ValueError):w.request(*args)
    assert w.state()==before


def test_incomplete_or_semantically_invalid_state_is_rejected(tmp_path):
    w=GameWorld();w.request('rain',2,2,duration=10);w.step(12)
    state=w.state()
    for mutate in (
        lambda d:d['game']['interventions'][0].update(status='active'),
        lambda d:d['game']['interventions'][0]['totals'].update(regenerated=99999),
        lambda d:d['events'].pop(next(i for i,e in enumerate(d['events']) if e['kind']=='divine_request')),
    ):
        data=copy.deepcopy(state);mutate(data)
        with pytest.raises(AssertionError):GameWorld.from_state(data)
    p=tmp_path/'incomplete.g1.sqlite'
    with sqlite3.connect(p) as db:
        from gnome_fortress.game_storage import APPLICATION_ID
        db.execute(f'PRAGMA application_id={APPLICATION_ID}');db.execute('PRAGMA user_version=1')
        db.execute('CREATE TABLE game_checkpoint (id,format,payload,sha256)')
    with pytest.raises(ValueError):load_game(p)


def test_actual_regeneration_activation_and_exclusive_expiry(monkeypatch):
    w=GameWorld();monkeypatch.setattr(w,'decide',lambda a:None)
    w.step(9)
    for row in w.cells:
        for c in row:
            if c.terrain in ('grass','forest'):c.food=10
    p=w.request('rain',1,1,0,10)
    w.step();assert w.cell(1,1).food==18 and p.status=='active'
    w.step(10)
    assert p.status=='expired' and p.expired_tick==20 and w.cell(1,1).food==22
    assert p.totals['pulses']==1 and p.totals['delta']==4
    w.validate()
