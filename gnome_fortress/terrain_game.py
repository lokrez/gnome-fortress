"""Opt-in gameplay generation 2. Legacy simulation and gameplay remain untouched."""
import copy
from dataclasses import asdict, dataclass, field

from .engine import World, TRAITS
from .game import GameWorld, Intervention, POWERS, DEFAULT_RADIUS, DEFAULT_DURATION
from .model import Event

FORMAT='gnome-fortress-terrain-g5-v1'
RECORD_VERSION=1
TERRAINS={'grass','forest','hazard','rock','water'}
TERRAIN_POWERS={'rupture':dict(source=('grass','forest'),result='hazard',radius=2),
                'rewild':dict(source=('hazard',),result='forest',radius=2),
                'wellspring':dict(source=('rock',),result='water',radius=0)}


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

    def request(self,kind,x,y,radius=None,duration=None):
        if kind in POWERS:
            p=super().request(kind,x,y,DEFAULT_RADIUS if radius is None else radius,
                              DEFAULT_DURATION if duration is None else duration)
            p=TerrainIntervention(**asdict(p));self.interventions[-1]=p
            return p
        if kind not in TERRAIN_POWERS:raise ValueError('Unknown terrain power')
        if self.extinct:raise ValueError('This world is extinct')
        radius=TERRAIN_POWERS[kind]['radius'] if radius is None else radius
        if any(type(v) is not int for v in (x,y,radius)) or not (0<=x<self.width and 0<=y<self.height and 0<=radius<=max(self.width,self.height)):
            raise ValueError('Invalid terrain target/radius')
        if kind=='wellspring' and radius!=0:raise ValueError('Wellspring affects a single rock tile')
        if duration is not None and (type(duration) is not int or duration!=0):raise ValueError('Terrain powers are one-shot, not timed')
        p=TerrainIntervention(len(self.interventions)+1,kind,self.tick,self.tick+1,x,y,radius,
            0,self.tick+1,dict(record_version=RECORD_VERSION))
        self.interventions.append(p)
        self.event('divine_request',intervention=p.id,power=kind,x=x,y=y,radius=radius,
            activation_tick=p.activation_tick,duration=0,expires_tick=p.expires_tick)
        return p

    def footprint(self,p):
        return [(x,y) for y in range(max(0,p.y-p.radius),min(self.height,p.y+p.radius+1))
                for x in range(max(0,p.x-p.radius),min(self.width,p.x+p.radius+1)) if p.contains(x,y)]

    def _apply_terrain(self,p,boundary):
        rule=TERRAIN_POWERS[p.kind]
        for x,y in self.footprint(p):
            c=self.cell(x,y)
            if c.terrain not in rule['source']:continue
            p.changes.append(dict(x=x,y=y,before_terrain=c.terrain,before_food=c.food,
                                  after_terrain=rule['result'],after_food=0))
            p.food_removed+=c.food;c.terrain=rule['result'];c.food=0
        p.changed_cells=len(p.changes);p.status='completed';p.completed_tick=boundary
        self.events.append(Event(boundary,'divine_terrain',None,None,
            dict(intervention=p.id,changed_cells=p.changed_cells,food_removed=p.food_removed)))

    def step(self,count=1):
        if type(count) is not int or count<0:raise ValueError('Tick count must be nonnegative integer')
        for _ in range(count):
            if self.extinct:break
            boundary=self.tick+1
            for p in self.interventions:
                if p.status=='queued' and p.activation_tick==boundary:
                    if p.kind in TERRAIN_POWERS:self._apply_terrain(p,boundary)
                    else:
                        p.status='active'
                        self.events.append(Event(boundary,'divine_active',None,None,dict(intervention=p.id)))
                elif p.status=='active' and p.expires_tick==boundary:
                    p.status='expired';p.expired_tick=boundary
                    self.events.append(Event(boundary,'divine_expired',None,None,dict(intervention=p.id)))
            World.step(self)

    def state(self):
        data=World.state(self)
        data['game']=dict(format=FORMAT,record_version=RECORD_VERSION,
            interventions=[asdict(p) for p in self.interventions],extinct_tick=self.extinct_tick,
            initial_terrain=copy.deepcopy(self.initial_terrain),origin=dict(self.origin))
        return data

    @classmethod
    def from_state(cls,data):
        if type(data.get('version')) is not int or data['version']!=1:raise ValueError('Unsupported simulation version')
        game=data.get('game',{})
        if game.get('format')!=FORMAT or type(game.get('record_version')) is not int or game.get('record_version')!=RECORD_VERSION:
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
        # The inherited validator uses assertions; refuse optimized execution rather
        # than silently omitting integrity checks under python -O.
        if not __debug__:raise ValueError('Terrain validation requires non-optimized Python')
        assert all(type(v) is int for v in (self.seed,self.width,self.height)) and self.width>=8 and self.height>=8
        World.validate(self)
        assert all(set(a.traits)==set(TRAITS) and all(type(v) is int for v in a.traits.values()) for a in self.agents.values())
        assert type(self.tick) is int and self.tick>=0
        assert self.extinct==(self.extinct_tick is not None)
        if self.extinct_tick is not None:assert self.extinct_tick==self.tick
        assert len(self.cells)==self.height and all(len(row)==self.width for row in self.cells)
        assert len(self.initial_terrain)==self.height and all(len(row)==self.width for row in self.initial_terrain)
        assert all(c.terrain in TERRAINS and type(c.food) is int and 0<=c.food<=100 for row in self.cells for c in row)
        assert all(t in TERRAINS for row in self.initial_terrain for t in row)
        assert type(self.origin['tick']) is int and 0<=self.origin['tick']<=self.tick
        if self.origin['kind']=='fresh':assert self.origin==dict(kind='fresh',tick=0)
        else:
            from .game import FORMAT as LEGACY_FORMAT
            assert set(self.origin)=={'kind','tick','format','digest'}
            assert self.origin['kind']=='legacy-import' and self.origin['format']==LEGACY_FORMAT
            assert len(self.origin['digest'])==64 and all(c in '0123456789abcdef' for c in self.origin['digest'])
        assert [p.id for p in self.interventions]==list(range(1,len(self.interventions)+1))
        assert [p.requested_tick for p in self.interventions]==sorted(p.requested_tick for p in self.interventions)
        histories={p.id:[] for p in self.interventions}
        assert all(type(e.tick) is int and 0<=e.tick<=self.tick for e in self.events)
        assert all(a.tick<=b.tick for a,b in zip(self.events,self.events[1:]))
        for e in self.events:
            if e.kind.startswith('divine_'):
                assert type(e.detail.get('intervention')) is int and e.detail['intervention'] in histories
                histories[e.detail['intervention']].append(e)
        terrain=copy.deepcopy(self.initial_terrain)
        terrain_execution=[]
        for p in self.interventions:
            assert p.kind in POWERS or p.kind in TERRAIN_POWERS
            assert all(type(v) is int for v in (p.id,p.requested_tick,p.activation_tick,p.x,p.y,p.radius,p.duration,p.expires_tick))
            assert 0<=p.requested_tick<=self.tick and p.activation_tick==p.requested_tick+1
            assert 0<=p.x<self.width and 0<=p.y<self.height and 0<=p.radius<=max(self.width,self.height)
            assert p.completed_tick is None or type(p.completed_tick) is int
            assert p.expired_tick is None or type(p.expired_tick) is int
            history=histories[p.id]
            request=[e for e in history if e.kind=='divine_request']
            assert len(request)==1 and request[0].tick==p.requested_tick
            assert all(type(request[0].detail[k]) is int for k in ('intervention','x','y','radius','activation_tick','duration','expires_tick'))
            assert request[0].detail==dict(intervention=p.id,power=p.kind,x=p.x,y=p.y,radius=p.radius,
                activation_tick=p.activation_tick,duration=p.duration,expires_tick=p.expires_tick)
            if p.kind in POWERS:
                assert p.parameters==POWERS[p.kind] and 1<=p.duration<=10000
                assert p.expires_tick==p.activation_tick+p.duration
                status='queued' if self.tick<p.activation_tick else 'active' if self.tick<p.expires_tick else 'expired'
                assert p.status==status and p.expired_tick==(p.expires_tick if status=='expired' else None)
                assert not p.changes and p.changed_cells==p.food_removed==0 and p.completed_tick is None
                assert all(e.kind in ('divine_request','divine_active','divine_expired','divine_regeneration') for e in history)
                assert [e.tick for e in history if e.kind=='divine_active']==([p.activation_tick] if self.tick>=p.activation_tick else [])
                assert [e.tick for e in history if e.kind=='divine_expired']==([p.expires_tick] if status=='expired' else [])
                totals=dict.fromkeys(('pulses','credited_cells','overridden_cells','regenerated','normal_regeneration','delta'),0)
                assert set(p.totals)==set(totals) and all(type(v) is int for v in p.totals.values())
                assert all(v>=0 for k,v in p.totals.items() if k!='delta')
                for e in history:
                    if e.kind in ('divine_active','divine_expired'):assert e.detail==dict(intervention=p.id)
                    if e.kind!='divine_regeneration':continue
                    assert e.tick%10==0 and p.activation_tick<=e.tick<p.expires_tick and e.tick<=self.tick
                    assert set(e.detail)==({'intervention'} | (set(totals)-{'pulses'}))
                    totals['pulses']+=1
                    for key in totals:
                        if key!='pulses':totals[key]+=e.detail[key]
                assert totals==p.totals and p.totals['delta']==p.totals['regenerated']-p.totals['normal_regeneration']
            else:
                assert p.parameters==dict(record_version=RECORD_VERSION) and type(p.parameters['record_version']) is int and p.duration==0
                if p.kind=='wellspring':assert p.radius==0
                assert p.expires_tick==p.activation_tick and p.expired_tick is None
                assert p.requested_tick>=self.origin['tick']
                completed=self.tick>=p.activation_tick
                assert p.status==('completed' if completed else 'queued')
                assert p.completed_tick==(p.activation_tick if completed else None)
                assert all(type(v) is int and v>=0 for v in (p.changed_cells,p.food_removed))
                assert all(type(v) is int for v in p.totals.values())
                assert p.totals==dict(pulses=0,credited_cells=0,overridden_cells=0,regenerated=0,normal_regeneration=0,delta=0)
                assert all(e.kind in ('divine_request','divine_terrain') for e in history)
                applied=[e for e in history if e.kind=='divine_terrain']
                assert len(applied)==int(completed)
                if not completed:
                    assert not p.changes and p.changed_cells==p.food_removed==0
                    continue
                assert applied[0].tick==p.activation_tick
                assert applied[0].detail==dict(intervention=p.id,changed_cells=p.changed_cells,food_removed=p.food_removed)
                terrain_execution.append(p.id)
                rule=TERRAIN_POWERS[p.kind]
                eligible=[(x,y) for x,y in self.footprint(p) if terrain[y][x] in rule['source']]
                assert [(c['x'],c['y']) for c in p.changes]==eligible
                assert p.changed_cells==len(p.changes) and p.food_removed==sum(c['before_food'] for c in p.changes)
                for c in p.changes:
                    assert set(c)=={'x','y','before_terrain','before_food','after_terrain','after_food'}
                    x,y=c['x'],c['y']
                    assert type(x) is int and type(y) is int
                    assert c['before_terrain']==terrain[y][x] and c['after_terrain']==rule['result']
                    assert type(c['before_food']) is int and 0<=c['before_food']<=100 and type(c['after_food']) is int and c['after_food']==0
                    if c['before_terrain'] not in ('grass','forest'):assert c['before_food']==0
                    terrain[y][x]=c['after_terrain']
        assert [e.detail['intervention'] for e in self.events if e.kind=='divine_terrain']==terrain_execution
        assert [[c.terrain for c in row] for row in self.cells]==terrain
