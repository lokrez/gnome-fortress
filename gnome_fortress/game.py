"""Opt-in G1 environmental interventions. Agent decisions remain inherited unchanged."""
import copy
from dataclasses import asdict, dataclass, field

from .engine import World
from .model import Event

FORMAT = 'gnome-fortress-game-g1-v1'
POWERS = {'rain': {'grass_bonus': 4, 'forest_bonus': 8},
          'drought': {'suppress_regeneration': True}}
DEFAULT_RADIUS = 5
DEFAULT_DURATION = 200


@dataclass
class Intervention:
    id: int
    kind: str
    requested_tick: int
    activation_tick: int
    x: int
    y: int
    radius: int
    duration: int
    expires_tick: int
    parameters: dict
    status: str = 'queued'
    expired_tick: int | None = None
    totals: dict = field(default_factory=lambda: dict(pulses=0, credited_cells=0,
        overridden_cells=0, regenerated=0, normal_regeneration=0, delta=0))

    def contains(self, x, y):
        return (self.x-x)**2 + (self.y-y)**2 <= self.radius**2


class GameWorld(World):
    def __init__(self, seed=1, width=48, height=32):
        self.interventions = []
        self.extinct_tick = None
        super().__init__(seed,width,height)

    @property
    def extinct(self):
        return not self._living_agents

    def request(self, kind, x, y, radius=DEFAULT_RADIUS, duration=DEFAULT_DURATION):
        if self.extinct:
            raise ValueError('This world is extinct; no further interventions')
        if kind not in POWERS:
            raise ValueError('Unknown divine power')
        if any(type(v) is not int for v in (x,y,radius,duration)):
            raise ValueError('Power coordinates, radius and duration must be integers')
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError('Target outside map')
        if not (0 <= radius <= max(self.width,self.height) and 1 <= duration <= 10000):
            raise ValueError('Invalid radius or duration (1..10000 ticks)')
        effect=Intervention(len(self.interventions)+1,kind,self.tick,self.tick+1,x,y,radius,
                            duration,self.tick+1+duration,copy.deepcopy(POWERS[kind]))
        self.interventions.append(effect)
        self.event('divine_request',intervention=effect.id,power=kind,x=x,y=y,radius=radius,
                   activation_tick=effect.activation_tick,duration=duration,expires_tick=effect.expires_tick)
        return effect

    def kill(self, agent, cause):
        super().kill(agent,cause)
        if self.extinct and self.extinct_tick is None:
            self.extinct_tick=self.tick

    def step(self, count=1):
        if type(count) is not int or count < 0:
            raise ValueError('Tick count must be a nonnegative integer')
        for _ in range(count):
            if self.extinct:
                break
            boundary=self.tick+1
            # Stable ID order; statuses refer to the upcoming complete tick.
            for effect in self.interventions:
                if effect.status=='queued' and effect.activation_tick==boundary:
                    effect.status='active'
                    self.events.append(Event(boundary,'divine_active',None,None,dict(intervention=effect.id)))
                elif effect.status=='active' and effect.expires_tick==boundary:
                    effect.status='expired';effect.expired_tick=boundary
                    self.events.append(Event(boundary,'divine_expired',None,None,dict(intervention=effect.id)))
            super().step()

    def _regenerate_food(self):
        active=[p for p in self.interventions if p.status=='active']
        if not active:
            return super()._regenerate_food()
        accounts={p.id:dict(credited_cells=0,overridden_cells=0,regenerated=0,normal_regeneration=0,delta=0) for p in active}
        for y,row in enumerate(self.cells):
            for x,cell in enumerate(row):
                if cell.terrain not in ('grass','forest'):
                    continue
                base=8 if cell.terrain=='forest' else 4
                normal=min(100,cell.food+base)-cell.food
                covering=[p for p in active if p.contains(x,y)]
                if not covering:
                    cell.food+=normal
                    continue
                droughts=[p for p in covering if p.kind=='drought']
                winner=(droughts or covering)[0]
                increase=0 if droughts else min(100,cell.food+base+winner.parameters[cell.terrain+'_bonus'])-cell.food
                for effect in covering:
                    account=accounts[effect.id]
                    if effect is winner:
                        account['credited_cells']+=1
                        account['regenerated']+=increase
                        account['normal_regeneration']+=normal
                        account['delta']+=increase-normal
                    else:
                        account['overridden_cells']+=1
                cell.food+=increase
        for effect in active:
            changes=accounts[effect.id];effect.totals['pulses']+=1
            for key,value in changes.items():effect.totals[key]+=value
            self.event('divine_regeneration',intervention=effect.id,**changes)

    def state(self):
        data=super().state()
        data['game']=dict(format=FORMAT,interventions=[asdict(p) for p in self.interventions],
                          extinct_tick=self.extinct_tick)
        return data

    @classmethod
    def from_state(cls,data):
        if data.get('game',{}).get('format')!=FORMAT:
            raise ValueError('Not a G1 gameplay checkpoint')
        world=super().from_state(copy.deepcopy(data))
        world.interventions=[Intervention(**p) for p in data['game']['interventions']]
        world.extinct_tick=data['game']['extinct_tick']
        world.validate()
        return world

    def validate(self):
        super().validate()
        assert len(self.slots)==60
        assert self.extinct==(self.extinct_tick is not None)
        if self.extinct_tick is not None:assert self.extinct_tick==self.tick
        assert [p.id for p in self.interventions]==list(range(1,len(self.interventions)+1))
        for p in self.interventions:
            assert p.kind in POWERS and p.parameters==POWERS[p.kind]
            assert all(type(v) is int for v in (p.id,p.requested_tick,p.activation_tick,p.x,p.y,p.radius,p.duration,p.expires_tick))
            assert 0<=p.requested_tick<=self.tick and p.activation_tick==p.requested_tick+1
            assert 0<=p.x<self.width and 0<=p.y<self.height
            assert 0<=p.radius<=max(self.width,self.height) and 1<=p.duration<=10000
            assert p.expires_tick==p.activation_tick+p.duration
            status='queued' if self.tick<p.activation_tick else 'active' if self.tick<p.expires_tick else 'expired'
            assert p.status==status
            assert p.expired_tick==(p.expires_tick if status=='expired' else None)
            assert set(p.totals)=={'pulses','credited_cells','overridden_cells','regenerated','normal_regeneration','delta'}
            assert all(type(v) is int for v in p.totals.values())
            assert all(v>=0 for k,v in p.totals.items() if k!='delta')
            assert p.totals['delta']==p.totals['regenerated']-p.totals['normal_regeneration']
        records={p.id: {'divine_request': [], 'divine_active': [], 'divine_expired': [], 'divine_regeneration': []}
                 for p in self.interventions}
        assert [p.requested_tick for p in self.interventions]==sorted(p.requested_tick for p in self.interventions)
        for event in self.events:
            if event.kind.startswith('divine_'):
                identity=event.detail['intervention']
                assert identity in records and event.kind in records[identity]
                records[identity][event.kind].append(event)
        for p in self.interventions:
            history=records[p.id]
            assert len(history['divine_request'])==1
            request=history['divine_request'][0]
            assert request.tick==p.requested_tick
            assert request.detail==dict(intervention=p.id,power=p.kind,x=p.x,y=p.y,radius=p.radius,
                activation_tick=p.activation_tick,duration=p.duration,expires_tick=p.expires_tick)
            assert [e.tick for e in history['divine_active']]==([p.activation_tick] if self.tick>=p.activation_tick else [])
            assert [e.tick for e in history['divine_expired']]==([p.expires_tick] if p.status=='expired' else [])
            totals=dict.fromkeys(p.totals,0)
            for event in history['divine_regeneration']:
                assert event.tick%10==0 and p.activation_tick<=event.tick<p.expires_tick and event.tick<=self.tick
                assert set(event.detail)==({'intervention'} | (set(totals)-{'pulses'}))
                totals['pulses']+=1
                for key in totals:
                    if key!='pulses':totals[key]+=event.detail[key]
            assert totals==p.totals
        assert all(0<=c.food<=100 for row in self.cells for c in row)
