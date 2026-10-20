import copy
import pytest
from gnome_fortress.engine import World
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game


def locate(w,terrain):return next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain==terrain)


@pytest.mark.parametrize('powers,result',[(['rupture','rewild'],'forest'),(['rewild','rupture'],'hazard')])
def test_exact_order_no_healing_displacement_or_resurrection(monkeypatch,powers,result):
    w=TerrainWorld();x,y=locate(w,'grass');a=w.agents[1];a.x=x;a.y=y;a.health=40
    w.kill(w.agents[2],'test');before=copy.deepcopy(World.state(w));rng=w.rng.getstate()
    monkeypatch.setattr(w,'_biology',lambda a:None);monkeypatch.setattr(w,'decide',lambda a:None)
    for name in powers:w.request(name,x,y,0)
    w.step();w.validate()
    assert w.cell(x,y).terrain==result
    assert w.rng.getstate()==rng and World.state(w)['agents']==before['agents']
    assert w.agents[2].died==0 and not w.agents[2].alive
    assert [e.detail['intervention'] for e in w.events if e.kind=='divine_terrain']==[1,2]
    if powers[0]=='rupture':
        assert [p.changed_cells for p in w.interventions]==[1,1]
        assert w.interventions[1].changes[0]['before_terrain']=='hazard'
    else:assert [p.changed_cells for p in w.interventions]==[0,1]


@pytest.mark.parametrize('weather,food',[('rain',16),('drought',0)])
def test_rewild_at_pulse_uses_existing_regeneration(monkeypatch,weather,food):
    w=TerrainWorld();w.step(9);x,y=locate(w,'hazard')
    monkeypatch.setattr(w,'decide',lambda a:None)
    w.request(weather,x,y,0,10);p=w.request('rewild',x,y,0);w.step()
    assert w.cell(x,y).terrain=='forest' and w.cell(x,y).food==food
    assert p.changes[0]['after_food']==0 and p.food_removed==0
    assert w.interventions[0].totals['regenerated']==food;w.validate()
    w.step(10)
    assert w.interventions[0].status=='expired' and w.cell(x,y).food==food+8
    w.validate()


def test_wellspring_existing_drink_mechanics_and_safe_noop(monkeypatch):
    w=TerrainWorld()
    x,y=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row)
             if c.terrain=='rock' and any(w.cell(nx,ny).terrain in ('grass','forest') for nx,ny in w.neighbors(x,y)))
    ax,ay=next((nx,ny) for nx,ny in w.neighbors(x,y) if w.cell(nx,ny).terrain in ('grass','forest'))
    a=w.agents[1];a.x=ax;a.y=ay;a.thirst=80
    before=[(b.id,b.x,b.y,b.health,b.alive) for b in w.agents.values()];rng=w.rng.getstate()
    monkeypatch.setattr(w,'_biology',lambda a:None)
    monkeypatch.setattr(w,'decide',lambda b:World.decide(w,b) if b.id==1 else None)
    p=w.request('wellspring',x,y);assert a.thirst==80
    w.step()
    assert w.cell(x,y).terrain=='water' and p.radius==0 and p.changed_cells==1
    assert a.thirst==10 and a.action=='drink' and a.memories[-1].action=='drink'
    assert before==[(b.id,b.x,b.y,b.health,b.alive) for b in w.agents.values()]
    assert w.rng.getstate()==rng;w.validate()
    again=w.request('wellspring',x,y);w.step();assert again.changed_cells==0
    p=w.request('wellspring',ax,ay);w.step();assert p.changed_cells==0
    with pytest.raises(ValueError):w.request('wellspring',x,y,1)
    w.validate()


def test_all_powers_queued_and_completed_replay(tmp_path):
    a=TerrainWorld(2);rock=locate(a,'rock')
    a.step(9)
    for name,x,y in [('rain',1,1),('rupture',1,1),('rewild',1,1),('drought',2,2),('wellspring',*rock)]:a.request(name,x,y)
    path=tmp_path/'mixed.g5.sqlite';save_game(a,path);b=load_game(path)
    a.step(31);b.step(31);assert a.state()==b.state();a.validate()
    save_game(b,path);c=load_game(path);a.step(40);c.step(40);assert a.state()==c.state()
    assert len([e for e in a.events if e.kind=='divine_terrain'])==3
    assert all(p.status=='completed' for p in a.interventions if p.kind in ('rupture','rewild','wellspring'))
