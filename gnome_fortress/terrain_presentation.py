"""Disposable G7 terrain indexes; authoritative records remain in TerrainWorld."""
from collections import Counter

from .game_presentation import EventIndex, MEANINGFUL, WorldPresentation, event_text
from .terrain_game import TERRAIN_POWERS


class TerrainEvents(EventIndex):
    def update(self,events):
        if events is not self.source or len(events)<self.seen:
            self.__init__(events);return len(self.positions)
        added=0
        while self.seen<len(events):
            if events[self.seen].kind in MEANINGFUL or events[self.seen].kind=='divine_terrain':
                self.positions.append(self.seen);added+=1
            self.seen+=1;self.records_examined+=1
        return added


class TerrainIndex:
    """O(new events + new transitions) updates; per-tile references, no biographies."""
    def __init__(self,world):
        self.world=world;self.source=world.events;self.seen=0;self.requests_seen=0
        self.by_tile={};self.altered=set();self.conversions=Counter();self.requests=Counter()
        self.records_examined=0;self.transitions_examined=0;self.latest=None
        self.update()

    def update(self):
        w=self.world
        if self.source is not w.events or len(w.events)<self.seen:
            self.__init__(w);return
        for p in w.interventions[self.requests_seen:]:self.requests[p.kind]+=1
        self.requests_seen=len(w.interventions)
        while self.seen<len(w.events):
            e=w.events[self.seen];self.seen+=1;self.records_examined+=1
            if e.kind!='divine_terrain':continue
            p=w.interventions[e.detail['intervention']-1];self.latest=p.id
            for index,c in enumerate(p.changes):
                xy=(c['x'],c['y']);self.by_tile.setdefault(xy,[]).append((p.id,index))
                self.conversions[p.kind]+=1;self.transitions_examined+=1
                if c['after_terrain']!=w.initial_terrain[c['y']][c['x']]:self.altered.add(xy)
                else:self.altered.discard(xy)

    def page(self,xy,start=0,count=5):
        return [(self.world.interventions[identity-1],self.world.interventions[identity-1].changes[index])
                for identity,index in self.by_tile.get(xy,[])[max(0,start):max(0,start)+count]]

    def summary(self):
        return dict(requests=dict(self.requests),conversions=dict(self.conversions),
            transitions=sum(self.conversions.values()),ever_transformed=len(self.by_tile),
            currently_altered=len(self.altered),latest=self.latest)

    def hazard_provenance(self,event):
        """Coordinate/tick attribution only; not a cause-of-death counterfactual."""
        if event.kind!='hazard' or 'x' not in event.detail or 'y' not in event.detail:return None
        xy=(event.detail['x'],event.detail['y'])
        for identity,index in reversed(self.by_tile.get(xy,[])):
            p=self.world.interventions[identity-1]
            if p.activation_tick<=event.tick:
                return p.id if p.changes[index]['after_terrain']=='hazard' else None
        return None


class TerrainPresentation(WorldPresentation):
    def __init__(self,world):
        self.world=world;self.events=TerrainEvents(world.events);self.key=None;self.status={}
        self.powers=[];self.active_powers=[];self.region_cells={};self.land=TerrainIndex(world)
        self.refresh()

    def refresh(self):
        previous=self.key;added=super().refresh();self.land.update()
        if previous!=self.key:
            for card,p in zip(self.powers,self.world.interventions):
                card.update(terrain=p.kind in TERRAIN_POWERS,changed_cells=p.changed_cells,
                            food_removed=p.food_removed,completed=p.completed_tick)
        return added


def terrain_event_text(event,world):
    if event.kind=='divine_terrain':
        p=world.interventions[event.detail['intervention']-1]
        return f'#{p.id} {p.kind} completed: {p.changed_cells} changed cells; food removed {p.food_removed}'
    return event_text(event,world)
