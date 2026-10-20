import copy
import pytest
from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game


def test_rupture_geometry_food_no_direct_damage(monkeypatch):
    w=TerrainWorld(1);w.step(9)
    a=w.agents[1];x,y=a.x,a.y
    expected=[(cx,cy) for cy in range(w.height) for cx in range(w.width)
              if (cx-x)**2+(cy-y)**2<=4 and w.cell(cx,cy).terrain in ('grass','forest')]
    before=copy.deepcopy(w.state());rng=w.rng.getstate()
    p=w.request('rupture',x,y)
    assert p.status=='queued' and p.radius==2 and p.duration==0
    # Isolate environmental activation from independent biology/movement.
    health=[a.health for a in w.agents.values()]
    monkeypatch.setattr(w,'_biology',lambda a:None);monkeypatch.setattr(w,'decide',lambda a:None)
    w.step();assert w.rng.getstate()==rng
    assert [a.health for a in w.agents.values()]==health
    assert [(c['x'],c['y']) for c in p.changes]==expected
    assert p.food_removed==sum(before['cells'][cy][cx]['food'] for cx,cy in expected)
    assert w.cell(x,y).terrain=='hazard' and (a.x,a.y)==(x,y)
    for cy,row in enumerate(w.cells):
        for cx,c in enumerate(row):
            if (cx,cy) in expected:assert c.terrain=='hazard' and c.food==0
            else:
                old=before['cells'][cy][cx]
                assert c.terrain==old['terrain']
                assert c.food==(min(100,old['food']+(8 if c.terrain=='forest' else 4)) if c.terrain in ('grass','forest') else old['food'])
    w.validate()
    again=w.request('rupture',x,y);w.step();assert not again.changes and again.food_removed==0
    w.validate()


def test_order_edge_noop_and_rain_preserved(monkeypatch):
    w=TerrainWorld(2);monkeypatch.setattr(w,'decide',lambda a:None)
    w.step(9);w.request('rain',0,0,5,20)
    a=w.request('rupture',0,0,2);b=w.request('rupture',1,0,2)
    w.step();w.validate()
    assert not ({(c['x'],c['y']) for c in a.changes}&{(c['x'],c['y']) for c in b.changes})
    assert [e.detail['intervention'] for e in w.events if e.kind=='divine_terrain']==[2,3]
    assert all(0<=c['x']<w.width and 0<=c['y']<w.height for p in (a,b) for c in p.changes)
    assert w.interventions[0].totals['pulses']==1
    water=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain=='water')
    p=w.request('rupture',*water,0);w.step();assert p.changed_cells==0;w.validate()


def test_schedule_replay_and_pending_active_save(tmp_path):
    a=TerrainWorld(3);a.step(9);a.request('rain',1,1);a.request('rupture',2,2)
    path=tmp_path/'pending.g5.sqlite';save_game(a,path);b=load_game(path)
    for w in (a,b):w.step(20);w.validate()
    assert a.state()==b.state()
    save_game(b,path);c=load_game(path);a.step(30);c.step(30);assert a.state()==c.state()


def test_no_terrain_matches_legacy_with_powers():
    a=GameWorld(4);b=TerrainWorld(4)
    for w in (a,b):w.step(9);w.request('rain',1,1);w.request('drought',3,3,2,10);w.step(70);w.validate()
    assert World.state(a)==World.state(b)
    assert [p.totals for p in a.interventions]==[p.totals for p in b.interventions]


@pytest.mark.parametrize('mutation',[
    lambda d:d['game']['interventions'][0]['changes'].pop(),
    lambda d:d['game']['interventions'][0].update(changed_cells=999),
    lambda d:d['game']['interventions'][0]['changes'][0].update(after_terrain='grass'),
    lambda d:d['game']['interventions'][0].update(status='active'),
    lambda d:d['events'].pop(next(i for i,e in enumerate(d['events']) if e['kind']=='divine_terrain')),
    lambda d:d['cells'][1][1].update(terrain='forest'),
])
def test_reject_invalid_terrain_chains(mutation):
    w=TerrainWorld();w.request('rupture',1,1);w.step();data=copy.deepcopy(w.state());mutation(data)
    with pytest.raises((AssertionError,ValueError)):TerrainWorld.from_state(data)


def test_invalid_requests_no_rng_or_mutation_and_extinction():
    w=TerrainWorld();before=w.state()
    for args in (('rupture',-1,1),('rupture',1,1,True),('rupture',1,1,2,10),('bad',1,1)):
        with pytest.raises(ValueError):w.request(*args)
        assert w.state()==before
    for a in list(w.living()):w.kill(a,'test')
    before=w.state();w.step(10);assert before==w.state()
    with pytest.raises(ValueError):w.request('rupture',1,1)
