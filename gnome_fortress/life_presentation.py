"""One disposable selected-individual history; no world writes or biography archive."""
from array import array
import heapq

from .game_presentation import agent_view


def event_role(event,identity):
    d=event.detail
    if event.kind=='birth':
        if event.actor==identity:return 'born'
        if identity in (d.get('parents') or ()):return 'parent'
    elif event.kind=='reproduce':
        if event.actor==identity:return 'parent (actor)'
        if event.target==identity:return 'parent (partner)'
        if d.get('child')==identity:return 'child'
    elif event.kind=='social':
        if event.actor==identity:return 'initiator'
        if event.target==identity:return 'recipient'
    elif event.kind in ('hazard','death') and event.actor==identity:
        return 'injured' if event.kind=='hazard' else 'deceased'
    return None


def life_event_text(event,identity):
    role=event_role(event,identity)
    if role is None:return 'No recorded involvement'
    d=event.detail
    if event.kind=='birth':
        return 'Own birth recorded' if role=='born' else f"Child #{event.actor} born (parent)"
    if event.kind=='reproduce':
        return f"Reproduction: #{event.actor} + #{event.target}, child #{d.get('child','unavailable')} ({role})"
    if event.kind=='social':
        return f'Social encounter #{event.actor} -> #{event.target} ({role})'
    if event.kind=='hazard':return f"Hazard injury: {d.get('damage','unavailable')} health lost"
    return f"Death: {d.get('cause','unavailable')}"


def member_view(world,identity,relation):
    a=world.agents.get(identity)
    if a is None:return dict(id=identity,relation=relation,status='record unavailable',born=None,died=None)
    return dict(id=identity,relation=relation,
        status='deceased' if not a.alive else 'sleeping' if a.sleep_until>world.tick else 'awake',
        born=a.born,died=a.died)


def life_summary(world,identity):
    view=agent_view(world,identity)
    if view is None:return None
    a=world.agents[identity]
    view.update(born=a.born,died=a.died,location_kind='current' if a.alive else 'final stored',
        relationships=heapq.nsmallest(3,a.relationships.items(),key=lambda pair:(-pair[1],pair[0])))
    return view


class LifeHistory:
    """O(events + identities) on selection, O(appends) thereafter, one identity only."""
    def __init__(self,world):
        self.world=world;self.identity=None;self.positions=array('Q')
        self.children=array('Q');self.parents=();self.seen=0;self.next_id=0
        self.source=world.events;self.agents_source=world.agents
        self.records_examined=0;self.agents_examined=0

    def select(self,identity):
        if identity==self.identity:return
        self.identity=identity;self.positions=array('Q');self.children=array('Q');self.seen=0
        self.source=self.world.events;self.agents_source=self.world.agents
        a=self.world.agents.get(identity)
        self.parents=tuple(a.parents) if a is not None else ()
        for a in self.world.agents.values():
            self.agents_examined+=1
            if identity in a.parents:self.children.append(a.id)
        self.next_id=self.world.next_id
        self.update()

    def update(self):
        w=self.world
        if self.identity is None:return
        if self.source is not w.events or len(w.events)<self.seen or self.agents_source is not w.agents or w.next_id<self.next_id:
            identity=self.identity;self.identity=None;self.select(identity);return
        while self.seen<len(w.events):
            if event_role(w.events[self.seen],self.identity) is not None:self.positions.append(self.seen)
            self.seen+=1;self.records_examined+=1
        for identity in range(self.next_id,w.next_id):
            a=w.agents.get(identity);self.agents_examined+=1
            if a is not None and self.identity in a.parents:self.children.append(identity)
        self.next_id=w.next_id

    def page(self,start=0,count=5):
        return [(i,self.source[i]) for i in self.positions[max(0,start):max(0,start)+count]]

    def family(self,start=0,count=5):
        return dict(parents=[member_view(self.world,i,'parent') for i in self.parents],
                    children=[member_view(self.world,i,'child') for i in self.children[max(0,start):max(0,start)+count]],
                    total_children=len(self.children))
