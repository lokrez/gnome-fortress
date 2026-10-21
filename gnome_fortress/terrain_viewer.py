"""Terrain-enabled God viewer, sharing G1–G4 controls and checkpoint loop."""
import pygame

from .game import DEFAULT_RADIUS, DEFAULT_DURATION
from .god_viewer import GodObserver, POWER_COLORS, INK, MUTED, GOLD, run as run_base
from .terrain_game import TERRAIN_POWERS
from .terrain_presentation import TerrainPresentation, terrain_event_text
from .terrain_advisor import TerrainAdvisor
from .terrain_checkpoint import TerrainCheckpointWorker

COLORS={**POWER_COLORS,'rupture':(239,109,90),'rewild':(111,210,140),'wellspring':(96,211,233)}


class TerrainObserver(GodObserver):
    presentation_class=TerrainPresentation
    advisor_class=TerrainAdvisor
    colors=COLORS
    tab_labels={**GodObserver.tab_labels,'terrain':'Land [T]'}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        pygame.display.set_caption('Gnome Fortress | God Complex terrain prototype')
        self.buttons={name:pygame.Rect(self.map_width+12+(i%3)*149,119+(i//3)*36,142,32)
                      for i,name in enumerate(('observe','rain','drought','rupture','rewild','wellspring'))}
        self.tabs={name:pygame.Rect(self.map_width+12+i*112,250,107,28)
                   for i,name in enumerate(('gnome','powers','life','terrain'))}
        self.land_button=self.tabs['terrain']
        self.advisor_button.y=self.event_rect.y+4
        self.tile_select=False;self.tile_xy=(self.world.agents[1].x,self.world.agents[1].y)
        self.tile_start=0;self.tile_tail=True;self.footprints=True
        self.notice='New format prototype | T land history | A advisor'
        if self.last_request:self.notice=''

    @property
    def tile_capacity(self):return max(1,(self.screen.get_height()-455)//58)

    def navigate(self,destination):
        if destination=='terrain':
            self.advisor.open=False;self.tab='terrain';self.tile_select=True;self.mode=None
            latest=self.presentation.land.latest
            if latest:
                p=self.world.interventions[latest-1]
                self.tile_xy=(p.changes[0]['x'],p.changes[0]['y']) if p.changes else (p.x,p.y)
            self.tile_start=0;self.tile_tail=True
        else:
            self.tile_select=False
            super().navigate(destination)

    def preview_radius(self):
        return TERRAIN_POWERS[self.mode]['radius'] if self.mode in TERRAIN_POWERS else DEFAULT_RADIUS

    def preview_cells(self):
        if not self.hover or not self.mode:return []
        x,y=self.hover;r=self.preview_radius()
        return [(cx,cy,self.world.cell(cx,cy).terrain in TERRAIN_POWERS[self.mode]['source'])
                for cy in range(max(0,y-r),min(self.world.height,y+r+1))
                for cx in range(max(0,x-r),min(self.world.width,x+r+1)) if (cx-x)**2+(cy-y)**2<=r*r] if self.mode in TERRAIN_POWERS else []

    def extra_input(self,event):
        if event.type==pygame.KEYDOWN:
            if event.key in (pygame.K_e,pygame.K_f,pygame.K_p):
                self.mode={pygame.K_e:'rupture',pygame.K_f:'rewild',pygame.K_p:'wellspring'}[event.key]
                self.tile_select=False;return True
            elif event.key==pygame.K_t:
                self.tile_select=not self.tile_select;self.mode=None
                self.tab='terrain' if self.tile_select else 'gnome';return True
            elif event.key==pygame.K_h:self.footprints=not self.footprints;return True
            elif event.key in (pygame.K_r,pygame.K_d,pygame.K_o,pygame.K_F1,pygame.K_F2,pygame.K_F3,pygame.K_w,pygame.K_TAB):self.tile_select=False
            elif self.tab=='terrain' and event.key in (pygame.K_LEFTBRACKET,pygame.K_RIGHTBRACKET,pygame.K_l):
                if event.key==pygame.K_l:self.tile_tail=True
                else:self.browse_tile(self.tile_capacity*(-1 if event.key==pygame.K_LEFTBRACKET else 1))
                return True
        elif event.type==pygame.MOUSEWHEEL and self.tab=='terrain' and getattr(event,'pos',self.pointer)[0]>=self.map_width:
            self.browse_tile(-event.y*3);return True
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==3:self.tile_select=False
        elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
            if self.land_button.collidepoint(event.pos):
                self.tile_select=not self.tile_select;self.mode=None;self.tab='terrain' if self.tile_select else 'gnome';return True
            xy=self.map_target(event.pos)
            if xy and self.mode in TERRAIN_POWERS:
                if self.saving:self.notice='Saving: wait for completion before casting.'
                elif self.world.extinct:self.notice='This world has ended.'
                else:
                    p=self.world.request(self.mode,*xy);self.last_request=p.id
                    self.notice='';self.tab='powers';self.power_offset=0
                return True
            elif xy and self.tile_select:
                self.tile_xy=xy;self.tile_start=0;self.tile_tail=True;self.tab='terrain';return True
            elif any(r.collidepoint(event.pos) for r in self.buttons.values()):self.tile_select=False
            elif any(r.collidepoint(event.pos) for r in self.tabs.values()):self.tile_select=False
        return False

    def browse_tile(self,amount):
        total=len(self.presentation.land.by_tile.get(self.tile_xy,[]));end=max(0,total-self.tile_capacity)
        start=end if self.tile_tail else self.tile_start
        self.tile_start=max(0,min(start+amount,end));self.tile_tail=self.tile_start==end

    def notice_text(self):
        if self.notice:return self.notice
        if self.last_request:
            p=self.world.interventions[self.last_request-1]
            if p.kind in TERRAIN_POWERS:
                return f'#{p.id} {p.kind}: {p.status} | actual changes {p.changed_cells}, food removed {p.food_removed}'
        return super().notice_text()

    def format_event(self,event):return terrain_event_text(event,self.world)

    def region(self,kind,x,y,radius,preview=False):
        if kind not in TERRAIN_POWERS:return super().region(kind,x,y,radius,preview)
        if not preview:return
        for cx,cy,eligible in self.preview_cells():
            rect=(cx*self.tile,cy*self.tile,self.tile-1,self.tile-1)
            pygame.draw.rect(self.screen,self.colors[kind] if eligible else (125,133,143),rect,2 if eligible else 1)

    def draw_map_overlay(self):
        if self.footprints:
            for (x,y),history in self.presentation.land.by_tile.items():
                p=self.world.interventions[history[-1][0]-1]
                pygame.draw.rect(self.screen,self.colors[p.kind],(x*self.tile+1,y*self.tile+1,4,4))
        if self.tab=='terrain':
            x,y=self.tile_xy
            pygame.draw.rect(self.screen,GOLD,(x*self.tile,y*self.tile,self.tile,self.tile),2)

    def draw_controls(self,x):
        for name,rect in self.buttons.items():
            selected=(name=='observe' and self.mode is None) or self.mode==name
            pygame.draw.rect(self.screen,(57,86,96) if selected else (33,45,53),rect,border_radius=5)
            self.label(name.title(),rect.x+12,rect.y+8,GOLD if selected else INK,self.font)
        description=(f'{self.mode.title()} | r{self.preview_radius()} | one-shot; permanent terrain' if self.mode in TERRAIN_POWERS else
                     f'{self.mode.title() if self.mode else "Observe"} | r{DEFAULT_RADIUS} | {DEFAULT_DURATION} ticks')
        self.label(description,x,193,GOLD)
        self.label('R/D/E/F/P cast | O observe | T land | H footprints',x,211,MUTED)
        self.label(self.notice_text(),x,230,GOLD)

    def draw_inspection(self,x):
        if self.tab!='terrain':return super().draw_inspection(x)
        for name,rect in self.tabs.items():
            pygame.draw.rect(self.screen,(28,39,46),rect,border_radius=4)
            self.label(self.tab_labels[name],rect.x+8,rect.y+6)
        tx,ty=self.tile_xy;c=self.world.cell(tx,ty);history=self.presentation.land.by_tile.get(self.tile_xy,[])
        self.label(f'LAND HISTORY | ({tx},{ty})',x,291,GOLD,self.font)
        self.label(f'Current terrain {c.terrain} | current food {c.food}',x,316)
        self.label(f'Format-epoch terrain: {self.world.initial_terrain[ty][tx]}',x,337,MUTED)
        self.label(f'{len(history)} recorded transitions'+(' | transformed more than once' if len(history)>1 else ''),x,358)
        self.label('Click map to inspect | H toggles footprint corner marks',x,382,MUTED)
        self.label('Red rupture | green rewild | blue spring | unmarked: natural' if self.footprints else 'Footprints OFF (H): no provenance marks shown',x,401,MUTED)
        total=len(history);end=max(0,total-self.tile_capacity)
        start=end if self.tile_tail else min(self.tile_start,end)
        for j,(p,change) in enumerate(self.presentation.land.page(self.tile_xy,start,self.tile_capacity)):
            y=433+j*58
            self.label(f'Tick {p.completed_tick} | #{p.id} {p.kind}',x,y,self.colors[p.kind])
            self.label(f"{change['before_terrain']} ({change['before_food']} food) -> {change['after_terrain']} ({change['after_food']} food)",x,y+20)
        if not history:self.label('No recorded divine terrain transition on this tile.',x,435)
        self.label('[ ] / wheel: history pages | L latest | F1-F3 return',x,self.screen.get_height()-18,MUTED)

    def draw_powers(self,x,y):
        cards=self.presentation.powers;end=max(0,len(cards)-self.power_offset)
        for j,p in enumerate(reversed(cards[max(0,end-self.power_capacity):end])):
            top=y+j*108
            pygame.draw.rect(self.screen,(29,39,46),(x-3,top-4,446,100),border_radius=5)
            self.label(f"#{p['id']} {p['kind'].title()} | {p['status']}"+(f" / {p['overlap']}" if p['overlap'] else ''),x+5,top,self.colors[p['kind']])
            self.label(f"{p['location']} radius {p['radius']} | activation {p['activation']}",x+5,top+19)
            if p['terrain']:
                self.label(f"Actual changed cells {p['changed_cells']} | food removed {p['food_removed']}",x+5,top+39)
                self.label('Queued is a request; completed records actual changes.',x+5,top+58,MUTED)
                self.label('One-shot; terrain persists. No direct gnome damage/healing.',x+5,top+76,MUTED)
            else:
                t=p['totals']
                self.label(f"{p['future_active_ticks']} ticks ahead | expires {p['expires']}",x+5,top+37,MUTED)
                self.label(f"Regenerated {t['regenerated']:+d} | ordinary {t['normal_regeneration']:+d}",x+5,top+55)
                self.label(f"Delta {t['delta']:+d} | overridden cell-pulses {t['overridden_cells']}",x+5,top+73)
        if not cards:self.label('No interventions recorded.',x,y,MUTED)
        self.label('Preview: bright eligible NOW; gray ineligible. Queues may change it.',x,self.screen.get_height()-35,MUTED)
        self.label('Wheel: older/newer | Space pause | +/- speed | S save | Esc exit',x,self.screen.get_height()-18,MUTED)


def run(*args,**kwargs):
    # G8A only changes presentation; retain the exact Saveguard run loop/worker.
    from .living_viewer import LivingObserver
    return run_base(*args,**kwargs,observer_class=LivingObserver,worker_class=TerrainCheckpointWorker)
