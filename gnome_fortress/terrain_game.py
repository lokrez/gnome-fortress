"""Opt-in gameplay generation 2. Legacy simulation and gameplay remain untouched."""
import copy
from dataclasses import asdict, dataclass, field

from .engine import World
from .game import GameWorld, Intervention

FORMAT='gnome-fortress-terrain-g5-v1'
RECORD_VERSION=1
TERRAINS={'grass','forest','hazard','rock','water'}


@dataclass
class TerrainIntervention(Intervention):
    changes: list = field(default_factory=list)
    changed_cells: int = 0
    food_removed: int = 0
    completed_tick: int | None = None


class TerrainWorld(GameWorld):
    def __init__(self,seed=1,width=48,height=32):
        super().__init__(seed,width,height)
        self.initial_terrain=[[c.terrain for c in row] for row in self.cells]
        self.origin=dict(kind='fresh',tick=0)

    def request(self,*args,**kwargs):
        p=super().request(*args,**kwargs)
        p=TerrainIntervention(**asdict(p));self.interventions[-1]=p
        return p

    def state(self):
        data=World.state(self)
        data['game']=dict(format=FORMAT,record_version=RECORD_VERSION,
            interventions=[asdict(p) for p in self.interventions],extinct_tick=self.extinct_tick,
            initial_terrain=copy.deepcopy(self.initial_terrain),origin=dict(self.origin))
        return data

    @classmethod
    def from_state(cls,data):
        game=data.get('game',{})
        if game.get('format')!=FORMAT or game.get('record_version')!=RECORD_VERSION:
            raise ValueError('Unsupported terrain gameplay format/record version')
        if set(game)!={'format','record_version','interventions','extinct_tick','initial_terrain','origin'}:
            raise ValueError('Incomplete/unknown terrain gameplay fields')
        world=World.from_state.__func__(cls,copy.deepcopy(data))
        world.interventions=[TerrainIntervention(**p) for p in game['interventions']]
        world.extinct_tick=game['extinct_tick']
        world.initial_terrain=copy.deepcopy(game['initial_terrain']);world.origin=dict(game['origin'])
        world.validate()
        return world

    @classmethod
    def from_legacy(cls,legacy):
        legacy.validate()
        data=legacy.state()
        data['game'].update(format=FORMAT,record_version=RECORD_VERSION,
            initial_terrain=[[c.terrain for c in row] for row in legacy.cells],
            origin=dict(kind='legacy-import',tick=legacy.tick,format=data['game']['format'],digest=legacy.digest()))
        data['game']['interventions']=[asdict(TerrainIntervention(**asdict(p))) for p in legacy.interventions]
        return cls.from_state(data)

    def validate(self):
        GameWorld.validate(self)
        assert len(self.cells)==self.height and all(len(row)==self.width for row in self.cells)
        assert len(self.initial_terrain)==self.height and all(len(row)==self.width for row in self.initial_terrain)
        assert all(c.terrain in TERRAINS for row in self.cells for c in row)
        assert [[c.terrain for c in row] for row in self.cells]==self.initial_terrain
        assert type(self.origin['tick']) is int and 0<=self.origin['tick']<=self.tick
        if self.origin['kind']=='fresh':assert self.origin==dict(kind='fresh',tick=0)
        else:
            from .game import FORMAT as LEGACY_FORMAT
            assert set(self.origin)=={'kind','tick','format','digest'}
            assert self.origin['kind']=='legacy-import' and self.origin['format']==LEGACY_FORMAT
            assert len(self.origin['digest'])==64 and all(c in '0123456789abcdef' for c in self.origin['digest'])
        for p in self.interventions:
            assert not getattr(p,'changes',[]) and getattr(p,'completed_tick',None) is None
