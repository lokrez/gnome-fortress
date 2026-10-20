"""Read-only, disposable G2 views. Nothing here is serialized into the world."""
from array import array

MEANINGFUL=frozenset(('birth','death','hazard','divine_request','divine_active','divine_expired'))


class EventIndex:
    """One initial pass, then only appended records; eight bytes per matching index."""
    def __init__(self,events):
        self.source=events
        self.positions=array('Q')
        self.seen=0
        self.records_examined=0
        self.update(events)

    def update(self,events):
        if events is not self.source or len(events)<self.seen:
            self.source=events;self.positions=array('Q');self.seen=0
        added=0
        while self.seen<len(events):
            if events[self.seen].kind in MEANINGFUL:
                self.positions.append(self.seen);added+=1
            self.seen+=1;self.records_examined+=1
        return added

    def page(self,offset=0,count=5):
        end=max(0,len(self.positions)-max(0,offset))
        start=max(0,end-count)
        return [(i,self.source[i]) for i in reversed(self.positions[start:end])]


def event_text(event,world):
    actor=f'Gnome {event.actor:05d}' if event.actor is not None else 'Agent unavailable'
    detail=event.detail
    if event.kind=='birth':
        parents=detail.get('parents',[])
        return f'{actor} born'+(' (founder)' if detail.get('founder') else f'; parents {", ".join(map(str,parents)) or "unavailable"}')
    if event.kind=='death':return f'{actor} died: {detail.get("cause","unavailable")}'
    if event.kind=='hazard':return f'{actor} hazard injury: {detail.get("damage","unavailable")} health lost'
    identity=detail.get('intervention')
    power=world.interventions[identity-1].kind if isinstance(identity,int) and 1<=identity<=len(world.interventions) else 'power unavailable'
    if event.kind=='divine_request':
        return f'#{identity} {detail.get("power",power)} requested at ({detail.get("x")},{detail.get("y")}), r{detail.get("radius")}'
    if event.kind=='divine_active':return f'#{identity} {power} activated'
    if event.kind=='divine_expired':return f'#{identity} {power} expired'
    return f'{event.kind}: recorded event'


def agent_view(world,identity):
    a=world.agents.get(identity)
    if a is None:return None
    status='deceased' if not a.alive else 'sleeping' if a.sleep_until>world.tick else 'awake'
    return dict(id=a.id,name=a.name,status=status,death_cause=a.death_cause,
        age=a.age,health=a.health,hunger=a.hunger,thirst=a.thirst,fatigue=a.fatigue,
        action=a.action,parents=tuple(a.parents),children=a.children,location=(a.x,a.y),
        traits=dict(a.traits),movement={k:v for k,v in sorted(a.learned.items()) if k.startswith('move:')},
        memories=tuple((m.tick,m.action,m.feature,m.reward) for m in a.memories[-3:]))


class WorldPresentation:
    def __init__(self,world):
        self.world=world
        self.events=EventIndex(world.events)
        self.key=None
        self.status={}
        self.powers=[]
        self.active_powers=[]
        self.region_cells={}
        self.refresh()

    def refresh(self):
        w=self.world;added=self.events.update(w.events)
        key=(w.tick,len(w.interventions),len(w.agents),len(w._living_agents))
        if key==self.key:return added
        self.key=key
        living=len(w._living_agents);born=len(w.agents)
        food=sum(c.food for row in w.cells for c in row)
        self.status=dict(tick=w.tick,living=living,born=born,deaths=born-living,
            net_population_change=living-60,food_stock=food,
            active=sum(p.status=='active' for p in w.interventions))
        # Same resource eligibility/precedence as G1; derive overlap at THIS tick,
        # not from the last pulse or from cumulative overridden-cell counts.
        active=[p for p in w.interventions if p.status=='active']
        covered={p.id:0 for p in active};winners={}
        for p in active:
            for y in range(max(0,p.y-p.radius),min(w.height,p.y+p.radius+1)):
                for x in range(max(0,p.x-p.radius),min(w.width,p.x+p.radius+1)):
                    if p.contains(x,y):
                        if w.cell(x,y).terrain in ('grass','forest'):covered[p.id]+=1
                        priority=(p.kind!='drought',p.id)
                        if (x,y) not in winners or priority<winners[x,y]:winners[x,y]=priority
        credited={p.id:0 for p in active}
        self.region_cells={}
        for (x,y),(is_rain,identity) in winners.items():
            self.region_cells[x,y]='rain' if is_rain else 'drought'
            if w.cell(x,y).terrain in ('grass','forest'):credited[identity]+=1
        self.powers=[]
        for p in w.interventions:
            overlap=''
            if p.status=='active':
                if not covered[p.id]:overlap='no producing cells'
                elif not credited[p.id]:overlap='overridden'
                elif credited[p.id]<covered[p.id]:overlap='partially overridden'
            self.powers.append(dict(id=p.id,kind=p.kind,status=p.status,overlap=overlap,
                location=(p.x,p.y),radius=p.radius,activation=p.activation_tick,expires=p.expires_tick,
                future_active_ticks=max(0,p.expires_tick-max(w.tick+1,p.activation_tick)),
                totals=dict(p.totals)))
        self.active_powers=sorted((p for p in self.powers if p['status']=='active'),
                                  key=lambda p:(p['kind']=='drought',p['id']))
        return added
