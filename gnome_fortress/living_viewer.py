"""G8A: a camera-driven, read-only window onto the existing terrain game."""
from collections import defaultdict
from functools import lru_cache
import math
import time
import pygame

from .camera import Camera
from .pixel_art import appearance,gnome_sprite,terrain_tile
from .terrain_viewer import TerrainObserver
from .terrain_game import TERRAIN_POWERS
from .game import DEFAULT_DURATION
from .god_viewer import INK,MUTED,GOLD,wrap
from .viewer import Observer
from .life_presentation import life_summary,life_event_text

BG=(20,29,35);PANEL=(28,41,47);LINE=(58,79,80);TEAL=(112,209,183)
ACTIONS={'born':'Born','eat':'Eating','drink':'Drinking','sleep':'Sleeping',
         'reproduce':'Reproduction','socialize':'Socializing','wait':'Waiting','move':'Moving','dead':'Dead'}
NEEDS=(('health','Health',100,False),('hunger','Hunger',150,True),
       ('thirst','Thirst',150,True),('fatigue','Fatigue',130,True))


@lru_cache(maxsize=1024)
def text_image(size,text,color):return pygame.font.Font(None,size).render(text,True,color)


def happening(event,world):
    d=event.detail;who=f'Gnome #{event.actor:05d}' if event.actor is not None else 'Individual unavailable'
    if event.kind=='birth':return who+' was born'+(' (founder).' if d.get('founder') else '.')
    if event.kind=='death':return who+f" died: {d.get('cause','cause unavailable')}."
    if event.kind=='hazard':return who+f" was injured on hazardous terrain ({d.get('damage','?')} health lost)."
    identity=d.get('intervention');p=world.interventions[identity-1] if type(identity) is int and 0<identity<=len(world.interventions) else None
    name=p.kind.title() if p else d.get('power','Intervention').title()
    if event.kind=='divine_terrain':return f"{name} #{identity} changed {d.get('changed_cells','?')} tiles."
    if event.kind=='divine_request':return f'{name} #{identity} requested; awaiting its activation tick.'
    if event.kind=='divine_active':return f'{name} #{identity} became active.'
    if event.kind=='divine_expired':return f'{name} #{identity} expired.'
    return event.kind+': recorded event.'


class LivingObserver(TerrainObserver):
    """UI state is disposable. The inherited Saveguard runner remains authoritative."""
    def __init__(self,world,rate=None,paused=False,window_size=None):
        super().__init__(world,rate,paused)
        desktop=pygame.display.get_desktop_sizes()[0]
        size=window_size or (min(1600,max(960,desktop[0]-80)),min(960,max(640,desktop[1]-100)))
        self.screen=pygame.display.set_mode(size,pygame.RESIZABLE)
        pygame.display.set_caption('Gnome Fortress | First Contact')
        self.font=pygame.font.Font(None,25);self.small=pygame.font.Font(None,21)
        self.inspector_open=size[0]>=1000;self.feed_mode=1;self.food_overlay=False
        self.follow_id=None;self.dragging=False;self.advisor_scroll=0;self.last_pick=None;self.population_key=None;self.occupants={};self.queued_key=None;self.queued_powers=()
        self.follow_note='';self.hits=[];self.feed_hits=[];self.ui_hits=[];self.advisor_hits=[]
        self.selected=next(iter(world._living_agents),self.selected)
        self.tab='gnome';self.detail_offset=0;self.camera=None
        self.layout(size)
        self.camera=Camera(world.width,world.height,self.viewport,24)
        fit=self.camera.minimum;self.camera.tile=next((n for n in self.camera.levels if n>=fit*1.4),96);self.camera.clamp()
        self.notice='Wheel: zoom • arrows: pan • click a gnome • C: follow • O: observe'
        self.sync()

    def layout(self,size):
        width,height=size
        self.text_size=26 if width>=2000 else 21;self.title_size=32 if width>=2000 else 25
        self.font=pygame.font.Font(None,self.title_size);self.small=pygame.font.Font(None,self.text_size)
        self.ui_hits=[];self.feed_hits=[]
        self.toolbar={};x=12;y=64
        options=[('observe','Observe O'),('rain','Rain R'),('drought','Drought D'),('rupture','Rupture E'),
                 ('rewild','Rewild F'),('wellspring','Spring P'),('advisor','Advisor A'),
                 ('pause','Pause / play'),('save','Save S'),('inspector','Inspect I'),('food','Food B')]
        for name,label in options:
            w=max(86,self.small.size(label)[0]+22)
            if x+w>width-12:x=12;y+=37
            self.toolbar[name]=(pygame.Rect(x,y,w,31),label);x+=w+6
        self.content_top=y+43
        panel_width=448 if width>=2000 else 352 if width>=1100 else 320
        right=width-panel_width-24 if self.inspector_open else width-12
        self.panel_rect=pygame.Rect(right+12,self.content_top,panel_width,height-self.content_top-32)
        self.event_rect=pygame.Rect(12,height-32-(184 if self.feed_mode==2 else 108 if self.feed_mode==1 else 0),right-12,
                                    184 if self.feed_mode==2 else 108 if self.feed_mode==1 else 0)
        self.viewport=pygame.Rect(12,self.content_top,right-12,max(80,self.event_rect.y-self.content_top-8))
        self.map_width=self.viewport.right
        if self.camera:self.camera.resize(self.viewport)
        self.feed_button=pygame.Rect(self.event_rect.right-98,self.event_rect.y+4,92,25)
        self.tabs={};names=[('gnome','Overview'),('details','Details'),('life','Life'),('family','Family'),
                            ('terrain','Land'),('powers','Powers'),('statistics','World')]
        gap=5;cell=(panel_width-16-gap*3)//4
        for i,(name,label) in enumerate(names):self.tabs[name]=(pygame.Rect(self.panel_rect.x+8+(i%4)*(cell+gap),self.content_top+(i//4)*33,cell,28),label)
        self.body=pygame.Rect(self.panel_rect.x+12,self.content_top+76,panel_width-24,self.panel_rect.height-88)

    @property
    def notice(self):return getattr(self,'_notice','')

    @notice.setter
    def notice(self,value):
        self._notice=value;self.notice_until=time.monotonic()+6

    @property
    def event_capacity(self):return max(1,(self.event_rect.h-32)//36)
    @property
    def life_capacity(self):return max(1,(self.body.h-95)//60) if hasattr(self,'body') else 1
    @property
    def family_capacity(self):return max(1,(self.body.h-238)//50) if hasattr(self,'body') else 1
    @property
    def power_capacity(self):return max(1,(self.body.h-45)//152) if hasattr(self,'body') else 1
    @property
    def tile_capacity(self):return max(1,(self.body.h-154)//58) if hasattr(self,'body') else 1

    def label(self,text,x,y,color=INK,font=None):
        size=self.title_size if font is self.font else self.text_size
        self.screen.blit(text_image(size,str(text),color),(round(x),round(y)))

    def paragraph(self,text,x,y,width,color=INK):
        for line in wrap(self.small,text,width):self.label(line,x,y,color);y+=20
        return y

    def sync(self):
        super().sync()
        if not hasattr(self,'camera') or self.camera is None:return
        if self.tab=='family':self.life.select(self.selected);self.life.update()
        if self.follow_id is not None:
            a=self.world.agents.get(self.follow_id)
            if a is None or not a.alive:
                self.follow_note=f'Follow stopped: #{self.follow_id} '+('died; final location retained.' if a else 'record unavailable.')
                self.follow_id=None
            else:self.camera.center_tile(a.x,a.y)
        queued_key=(self.world.tick,len(self.world.interventions))
        if queued_key!=self.queued_key:
            self.queued_key=queued_key;self.queued_powers=tuple(p for p in self.world.interventions if p.status=='queued')
        key=(self.world.tick,len(self.world._living_agents),self.world.next_id)
        if key!=self.population_key:
            groups=defaultdict(list)
            for a in self.world._living_agents.values():groups[a.x,a.y].append(a.id)
            self.occupants=dict(groups);self.population_key=key

    def select_individual(self,identity):
        previous=self.selected
        result=super().select_individual(identity)
        if result and previous!=identity:
            self.follow_id=None;self.follow_note='';self.detail_offset=0
        return result

    def center_selected(self):
        a=self.world.agents.get(self.selected)
        if a:self.camera.center_tile(a.x,a.y)

    def toggle_follow(self):
        a=self.world.agents.get(self.selected)
        if self.follow_id is not None:self.follow_id=None;self.follow_note='Camera follow stopped.'
        elif a and a.alive:self.follow_id=a.id;self.follow_note='';self.center_selected()
        else:self.follow_note='A deceased or unavailable individual cannot be followed live.'

    def navigate(self,destination):
        self.advisor.open=False;self.inspector_open=True;self.tile_select=False;self.mode=None
        if destination in ('life','family'):self.tab=destination;self.life.select(self.selected);self.life.update()
        elif destination=='terrain':
            self.tab='terrain';self.mode=None;self.tile_select=True
            latest=self.presentation.land.latest
            if latest:
                p=self.world.interventions[latest-1];self.tile_xy=(p.x,p.y)
            self.tile_start=0;self.tile_tail=True
        elif destination=='events':self.feed_mode=2;self.event_offset=0
        else:self.tab=destination if destination in ('powers','statistics','details') else 'gnome'
        self.layout(self.screen.get_size())

    def map_target(self,pos):return self.camera.screen_to_world(pos) if self.camera else None

    def set_mode(self,mode):
        self.follow_note=''
        self.mode=mode;self.tile_select=False;self.advisor.open=False
        if mode:self.notice=f'{mode.title()} ARMED • click map to request • O or right-click cancels'
        else:self.notice='Observation • click a gnome or a tile; repeat a crowd click to cycle occupants.'

    def button(self,rect,label,action,active=False):
        pygame.draw.rect(self.screen,(52,87,84) if active else (42,58,65),rect,border_radius=5)
        pygame.draw.rect(self.screen,TEAL if active else LINE,rect,1,border_radius=5)
        while self.small.size(label)[0]>rect.w-12 and len(label)>3:label=label[:-4]+'...'
        image=text_image(self.text_size,label,GOLD if active else INK)
        self.screen.blit(image,(rect.centerx-image.get_width()//2,rect.centery-image.get_height()//2))
        hit=rect.clip(self.screen.get_clip())
        if hit.w and hit.h:self.ui_hits.append((hit,action))

    def action(self,name):
        if name in ('observe','rain','drought','rupture','rewild','wellspring'):self.set_mode(None if name=='observe' else name)
        elif name=='advisor':
            opened=self.advisor.open;self.set_mode(None)
            self.advisor.open=False if opened else True
            if not opened:self.advisor.start();self.advisor_scroll=0
            self.inspector_open=True;self.layout(self.screen.get_size())
        elif name=='pause':self.paused=not self.paused;self.accumulator=0
        elif name=='save':self.save_requested=True
        elif name=='inspector':
            self.inspector_open=not self.inspector_open
            if not self.inspector_open:self.advisor.open=False
            self.layout(self.screen.get_size())
        elif name=='food':self.food_overlay=not self.food_overlay
        elif name=='feed':self.feed_mode=1 if self.feed_mode==2 else 2;self.layout(self.screen.get_size())
        elif name=='watch':self.toggle_watch()
        elif name=='center':self.center_selected()
        elif name=='follow':self.toggle_follow()
        elif name.startswith('tab:'):
            self.set_mode(None);self.tab=name[4:];self.advisor.open=False
            if self.tab=='terrain':self.set_mode(None);self.tile_select=True
            else:self.tile_select=False
        elif name.startswith('member:'):
            if self.select_individual(int(name[7:])):self.tab='gnome';self.center_selected()
            else:self.notice='This family identity is recorded, but its individual record is unavailable.'
        elif name.startswith('advisor:'):self.advisor_choice(name[8:])

    def handle(self,events):
        self.sync()
        for e in events:
            if e.type in (pygame.VIDEORESIZE,):
                size=(max(800,e.w),max(600,e.h));self.screen=pygame.display.set_mode(size,pygame.RESIZABLE)
                self.layout(size);continue
            if e.type==pygame.QUIT:self.running=False;continue
            if e.type==pygame.MOUSEMOTION:
                if self.dragging and hasattr(e,'rel'):
                    self.follow_id=None;self.camera.pan(-e.rel[0],-e.rel[1])
                self.pointer=e.pos;self.hover=self.map_target(e.pos);continue
            if e.type==pygame.MOUSEBUTTONUP and e.button==2:self.dragging=False;continue
            if e.type==pygame.KEYDOWN:
                k=e.key
                # Exit, pause and persistence remain available in every panel.
                if k in (pygame.K_ESCAPE,pygame.K_SPACE,pygame.K_s,pygame.K_EQUALS,pygame.K_PLUS,pygame.K_MINUS,pygame.K_PERIOD):
                    Observer.handle(self,[e]);continue
                if k==pygame.K_a:self.action('advisor');continue
                if self.advisor.open:
                    if pygame.K_0<=k<=pygame.K_9:self.advisor_choice(str(k-pygame.K_0))
                    continue
                powers={pygame.K_r:'rain',pygame.K_d:'drought',pygame.K_e:'rupture',pygame.K_f:'rewild',pygame.K_p:'wellspring',pygame.K_o:None}
                if k in powers:self.set_mode(powers[k]);continue
                if k in (pygame.K_LEFT,pygame.K_RIGHT,pygame.K_UP,pygame.K_DOWN):
                    self.follow_id=None;self.follow_note='';self.camera.pan(64*((k==pygame.K_RIGHT)-(k==pygame.K_LEFT)),64*((k==pygame.K_DOWN)-(k==pygame.K_UP)));continue
                if k==pygame.K_c:self.toggle_follow()
                elif k==pygame.K_HOME:self.follow_id=None;self.camera.fit()
                elif k==pygame.K_i:self.action('inspector')
                elif k==pygame.K_b:self.food_overlay=not self.food_overlay
                elif k==pygame.K_h:self.footprints=not self.footprints
                elif k==pygame.K_v:self.feed_mode=(self.feed_mode+1)%3;self.layout(self.screen.get_size())
                elif k==pygame.K_w:self.set_mode(None);self.toggle_watch();self.inspector_open=True;self.layout(self.screen.get_size())
                elif k==pygame.K_t:
                    was=self.tile_select;self.set_mode(None);self.tile_select=not was;self.tab='terrain' if self.tile_select else 'gnome';self.inspector_open=True;self.layout(self.screen.get_size())
                elif k in (pygame.K_F1,pygame.K_F2,pygame.K_F3):
                    self.navigate({pygame.K_F1:'gnome',pygame.K_F2:'powers',pygame.K_F3:'life'}[k])
                elif k==pygame.K_TAB:
                    ids=list(self.world.agents);index=ids.index(self.selected) if self.selected in self.world.agents else -1
                    self.select_individual(ids[(index+1)%len(ids)] if ids else None)
                elif k==pygame.K_END:self.event_offset=0
                elif k in (pygame.K_PAGEUP,pygame.K_PAGEDOWN):self.browse_events(self.event_capacity*(1 if k==pygame.K_PAGEUP else -1))
                elif k in (pygame.K_LEFTBRACKET,pygame.K_RIGHTBRACKET):self.scroll_panel(-1 if k==pygame.K_LEFTBRACKET else 1)
                elif k==pygame.K_l:self.life_tail=True;self.tile_tail=True
                continue
            if e.type==pygame.MOUSEWHEEL:
                pos=getattr(e,'pos',self.pointer)
                if self.advisor.open:
                    if self.panel_rect.collidepoint(pos):self.advisor_scroll=max(0,self.advisor_scroll-e.y*3)
                    continue
                if self.event_rect.collidepoint(pos):self.browse_events(e.y*3)
                elif self.inspector_open and self.panel_rect.collidepoint(pos):self.scroll_panel(-e.y)
                elif self.viewport.collidepoint(pos):
                    self.camera.zoom(e.y,self.viewport.center if self.follow_id is not None else pos)
                    self.hover=self.map_target(pos)
                continue
            if e.type==pygame.MOUSEBUTTONDOWN:
                self.pointer=e.pos;self.hover=self.map_target(e.pos)
                if e.button==2:
                    self.dragging=self.viewport.collidepoint(e.pos) and not self.advisor.open;continue
                if e.button==3:self.set_mode(None);continue
                if e.button!=1:continue
                # Toolbar and inspector are explicit hit regions, never map aliases.
                static=[(r,n) for n,(r,label) in self.toolbar.items()]
                if self.inspector_open:static += [(r,'tab:'+n) for n,(r,label) in self.tabs.items()]
                dynamic=[(r,n) for r,n in self.ui_hits if (n.startswith('advisor:') and self.advisor.open) or
                         (not self.advisor.open and ((n in ('follow','center') and self.tab=='gnome') or
                          (n=='watch' and self.tab in ('life','family')) or (n.startswith('member:') and self.tab=='family') or n=='feed'))]
                chosen=next((name for rect,name in reversed(static+dynamic) if rect.collidepoint(e.pos)),None)
                if chosen:self.action(chosen);continue
                if self.advisor.open:continue
                feed=next((event for rect,event in self.feed_hits if rect.collidepoint(e.pos)),None)
                if feed is not None:self.open_event(feed);continue
                xy=self.map_target(e.pos)
                if xy is None:continue
                if self.mode:
                    if self.saving:self.notice='Saving shared state; casting is temporarily unavailable.'
                    elif self.world.extinct:self.notice='This world has ended. Inspection remains available.'
                    else:
                        p=self.world.request(self.mode,*xy);self.last_request=p.id;self.tab='powers';self.power_offset=0;self.notice=f'#{p.id} {p.kind} accepted for tick {p.activation_tick}; not yet applied.'
                        self.inspector_open=True;self.layout(self.screen.get_size())
                elif self.tile_select:self.tile_xy=xy;self.tile_start=0;self.tile_tail=True;self.tab='terrain'
                elif not self.pick_gnome(e.pos):
                    self.tile_xy=xy;self.tile_start=0;self.tile_tail=True;self.tab='terrain';self.inspector_open=True;self.layout(self.screen.get_size())
        self.hover=self.map_target(self.pointer)

    def scroll_panel(self,amount):
        if self.tab=='terrain':self.browse_tile(amount*self.tile_capacity)
        elif self.tab=='powers':self.power_offset=max(0,min(self.power_offset+amount,max(0,len(self.world.interventions)-self.power_capacity)))
        elif self.tab=='family':
            self.life.select(self.selected);self.life.update();self.family_start=max(0,min(self.family_start+amount*self.family_capacity,max(0,len(self.life.children)-self.family_capacity)))
        elif self.tab=='life':self.browse_life(amount*self.life_capacity)
        elif self.tab=='details':self.detail_offset=max(0,self.detail_offset+amount*3)

    def open_event(self,event):
        if event.actor is not None:
            if self.select_individual(event.actor):self.navigate('life')
            else:self.notice=f'Recorded individual #{event.actor} is unavailable.'
        identity=event.detail.get('intervention')
        p=self.world.interventions[identity-1] if type(identity) is int and 0<identity<=len(self.world.interventions) else None
        if p:self.tab='powers';self.power_offset=len(self.world.interventions)-identity;self.inspector_open=True
        x,y=event.detail.get('x'),event.detail.get('y')
        if type(x) is int and type(y) is int and 0<=x<self.world.width and 0<=y<self.world.height:
            self.follow_id=None;self.camera.center_tile(x,y);self.notice=f'Event tick {event.tick}: centered recorded coordinates ({x}, {y}).'
        elif p:
            self.follow_id=None;self.camera.center_tile(p.x,p.y);self.notice=f'#{p.id}: centered recorded intervention target.'
        elif event.actor in self.world.agents:
            self.follow_id=None;self.center_selected();a=self.world.agents[event.actor]
            self.notice=f'Event location not recorded; showing '+('current' if a.alive else 'final stored')+' individual location.'
        else:self.notice=(f'Individual #{event.actor} unavailable; no recorded location or target.' if event.actor is not None else 'No location or target record available for this event.')
        self.layout(self.screen.get_size())

    def sprite_layout(self):
        self.sync();x0,y0,x1,y1=self.camera.visible_bounds();t=self.camera.tile;items=[];counts=[]
        for (x,y),ids in self.occupants.items():
            if not(x0<=x<x1 and y0<=y<y1):continue
            visible=ids[:9] if t>=20 else ids[:1]
            if self.selected in ids and self.selected not in visible:visible=visible[:-1]+[self.selected]
            for j,identity in enumerate(visible):
                a=self.world.agents[identity];asleep=a.sleep_until>self.world.tick
                phase=(self.world.tick+identity)%2 if a.action=='move' and not asleep and not self.paused else 0
                size=max(10,round(t*.9));image,mask=gnome_sprite(appearance(identity),asleep,size,phase)
                cell=self.camera.tile_rect(x,y)
                dx=((j%3)-1)*t*.22 if len(visible)>1 else 0;dy=((j//3)-1)*t*.19 if len(visible)>1 else 0
                rect=image.get_rect(midbottom=(round(cell.centerx+dx),round(cell.centery+size*.46+dy)))
                items.append((identity,image,mask,rect))
            if len(ids)>1:counts.append((self.camera.tile_rect(x,y),len(ids)))
        items.sort(key=lambda item:(item[0]==self.selected,item[3].bottom,item[0]))
        return items,counts

    def selection_tag(self,items):
        a=self.world.agents.get(self.selected)
        if a is None:return None
        tile=self.camera.tile_rect(a.x,a.y)
        if not tile.colliderect(self.viewport):return None
        selected=next((item[3] for item in items if item[0]==a.id),tile.inflate(-max(1,self.camera.tile//3),-max(1,self.camera.tile//3)))
        tag=f'#{a.id:05d}'+(' • FINAL LOCATION' if not a.alive else ' • FOLLOW' if self.follow_id==a.id else '')
        image=text_image(21,tag,GOLD);r=self.viewport
        tx=max(r.x,min(r.right-image.get_width()-6,selected.centerx-image.get_width()/2));ty=max(r.y,selected.top-22)
        return pygame.Rect(tx-3,ty,image.get_width()+6,20),image,selected

    def pick_gnome(self,pos):
        items,_=self.sprite_layout();hit=None
        tag=self.selection_tag(items)
        if tag and (tag[0].collidepoint(pos) or
                    (tag[2].inflate(6,6).collidepoint(pos) and not tag[2].inflate(2,2).collidepoint(pos)) or
                    (not self.world.agents[self.selected].alive and tag[2].collidepoint(pos))):
            hit=self.selected
            if not self.world.agents[hit].alive:
                self.navigate('life');self.notice='Final stored location; this individual is deceased.';return True
        for identity,image,mask,rect in reversed(items) if hit is None else []:
            if rect.collidepoint(pos) and mask.get_at((pos[0]-rect.x,pos[1]-rect.y)):
                hit=identity;break
        xy=(self.world.agents[hit].x,self.world.agents[hit].y) if hit else self.map_target(pos)
        ids=self.occupants.get(xy,[])
        if not ids:return False
        repeated=self.last_pick is not None and self.last_pick[0]==xy and math.dist(self.last_pick[1],pos)<4
        identity=ids[(ids.index(self.selected)+1)%len(ids)] if repeated and self.selected in ids else hit or ids[0]
        self.select_individual(identity);self.last_pick=(xy,pos);self.tab='gnome';self.inspector_open=True
        self.notice=f'#{identity:05d} selected'+(f' • {len(ids)} on this tile; click again to cycle (visual offsets only).' if len(ids)>1 else '.')
        self.layout(self.screen.get_size());return True

    def draw_world(self):
        r=self.viewport;pygame.draw.rect(self.screen,(32,51,52),r);self.screen.set_clip(r)
        x0,y0,x1,y1=self.camera.visible_bounds();t=self.camera.tile
        for y in range(y0,y1):
            for x in range(x0,x1):
                c=self.world.cell(x,y);rect=self.camera.tile_rect(x,y)
                self.screen.blit(terrain_tile(c.terrain,(x*13+y*7)%4,t),rect)
                if self.food_overlay and c.terrain in ('grass','forest'):
                    pygame.draw.rect(self.screen,(29,45,34),(rect.x+1,rect.bottom-4,t-2,3))
                    pygame.draw.rect(self.screen,(212,232,128),(rect.x+1,rect.bottom-4,round((t-2)*c.food/100),3))
                kind=self.presentation.region_cells.get((x,y))
                if kind:
                    pygame.draw.rect(self.screen,self.colors[kind],rect,1)
                    if t>=20:pygame.draw.line(self.screen,self.colors[kind],(rect.x+3,rect.y+3),(rect.x+3,rect.y+7))
                history=self.presentation.land.by_tile.get((x,y))
                if self.footprints and history:
                    p=self.world.interventions[history[-1][0]-1]
                    pygame.draw.rect(self.screen,self.colors[p.kind],(rect.right-max(4,t//5),rect.y,max(4,t//5),max(4,t//5)))
        for p in self.queued_powers:self.draw_region(p.kind,p.x,p.y,p.radius,False)
        if self.mode and self.hover:self.draw_region(self.mode,*self.hover,self.preview_radius(),True)
        if self.tab=='terrain':pygame.draw.rect(self.screen,GOLD,self.camera.tile_rect(*self.tile_xy),2)
        self.hits,counts=self.sprite_layout()
        for identity,image,mask,rect in self.hits:
            self.screen.blit(image,rect)
            a=self.world.agents[identity]
            if a.sleep_until>self.world.tick and t>=20:self.label('z',rect.right-2,rect.y-6,(211,232,252))
        for rect,count in counts:
            if t>=16:
                number=text_image(18,str(count),(255,249,214));bg=number.get_rect(topright=(rect.right,rect.bottom))
                pygame.draw.rect(self.screen,BG,bg);self.screen.blit(number,bg)
        a=self.world.agents.get(self.selected)
        if a:
            tile=self.camera.tile_rect(a.x,a.y)
            if tile.colliderect(r):
                selected=next((item[3] for item in self.hits if item[0]==a.id),tile.inflate(-max(1,t//3),-max(1,t//3)))
                pygame.draw.rect(self.screen,BG,selected.inflate(7,7),3,border_radius=3)
                pygame.draw.rect(self.screen,GOLD,selected.inflate(6,6),2,border_radius=3)
                if not a.alive:
                    pygame.draw.line(self.screen,GOLD,selected.topleft,selected.bottomright,2)
                    pygame.draw.line(self.screen,GOLD,selected.topright,selected.bottomleft,2)
                tag=self.selection_tag(self.hits)
                if tag:
                    tag_rect,image,_=tag;pygame.draw.rect(self.screen,BG,tag_rect)
                    self.screen.blit(image,(tag_rect.x+3,tag_rect.y))

        if self.hover:
            c=self.world.cell(*self.hover);txt=f'{self.hover} • {c.terrain.title()} • food {c.food}/100'
            n=len(self.occupants.get(self.hover,[]))
            if n:txt+=f' • {n} living; repeat click cycles'
            image=text_image(21,txt,INK);pygame.draw.rect(self.screen,BG,(r.x+8,r.bottom-28,min(r.w-16,image.get_width()+12),24));self.screen.blit(image,(r.x+14,r.bottom-25))
        self.screen.set_clip(None);pygame.draw.rect(self.screen,LINE,r,1)

    def footprint_cells(self,kind,x,y,radius):
        source=TERRAIN_POWERS[kind]['source'] if kind in TERRAIN_POWERS else ('grass','forest')
        return [(cx,cy,self.world.cell(cx,cy).terrain in source)
                for cy in range(max(0,y-radius),min(self.world.height,y+radius+1))
                for cx in range(max(0,x-radius),min(self.world.width,x+radius+1))
                if (cx-x)**2+(cy-y)**2<=radius*radius]

    def preview_cells(self):
        return self.footprint_cells(self.mode,*self.hover,self.preview_radius()) if self.mode and self.hover else []

    def draw_region(self,kind,x,y,radius,preview):
        for cx,cy,eligible in self.footprint_cells(kind,x,y,radius):
            rect=self.camera.tile_rect(cx,cy)
            if not rect.colliderect(self.viewport):continue
            color=self.colors[kind] if eligible or not preview else (162,163,161)
            pygame.draw.rect(self.screen,color,rect,2 if preview else 1)
            if preview and eligible:pygame.draw.rect(self.screen,INK,rect.inflate(-6,-6),1)
            elif preview:pygame.draw.line(self.screen,color,rect.topleft,rect.bottomright,1)
            elif self.camera.tile>=20:self.label('Q',rect.x+3,rect.y+2,color)

    def draw_card(self):
        r=self.body;x,y=r.topleft;a=self.world.agents.get(self.selected)
        if a is None:self.paragraph('Individual record unavailable. Select a living gnome or a recorded event.',x,y,r.w);return
        status='Deceased' if not a.alive else 'Sleeping' if a.sleep_until>self.world.tick else 'Awake'
        image,_=gnome_sprite(appearance(a.id),a.alive and a.sleep_until>self.world.tick,60,0)
        self.screen.blit(image,(x,y));self.label(a.name,x+60,y,GOLD,self.font);self.label(status,x+60,y+27)
        self.button(pygame.Rect(x+60,y+51,85,26),'Center','center')
        self.button(pygame.Rect(x+152,y+51,r.w-152,26),('Unfollow' if self.follow_id==a.id else 'Follow C') if a.alive else 'Life F3','follow' if a.alive else 'tab:life',self.follow_id==a.id)
        y+=92
        self.label('Latest recorded action',x,y,MUTED);y+=23
        self.label(ACTIONS.get(a.action,a.action),x,y,TEAL,self.font);y+=30
        for key,label,maximum,high_bad in NEEDS:
            value=getattr(a,key);self.label(f'{label} {value}'+(f' / {maximum}' if key=='health' else f'  (0–{maximum})'),x,y)
            bar=pygame.Rect(x,y+20,r.w,7);pygame.draw.rect(self.screen,(15,23,27),bar,border_radius=2)
            amount=max(0,min(1,value/maximum));color=(224,151,99) if (high_bad and value>100) or (not high_bad and value<30) else TEAL
            pygame.draw.rect(self.screen,color,(bar.x,bar.y,round(bar.w*amount),bar.h),border_radius=2);y+=36
        y=self.paragraph(f'Age {a.age} ticks • born tick {a.born}',x,y+3,r.w)
        y=self.paragraph(f'{"Current" if a.alive else "Final stored"} location ({a.x}, {a.y})',x,y+3,r.w)
        if not a.alive:y=self.paragraph(f'Died tick {a.died}: {a.death_cause or "cause unavailable"}',x,y+3,r.w,GOLD)
        parents=', '.join(f'#{i:05d}' for i in a.parents) or 'none (founder)'
        y=self.paragraph('Parents: '+parents,x,y+4,r.w)
        y=self.paragraph(f'Children: {a.children} recorded • Family tab links actual records',x,y+3,r.w)
        if y+40<r.bottom:self.paragraph('Action is the latest decision, not a continuous intention. Needs have different scales.',x,y+8,r.w,MUTED)

    def draw_details(self):
        a=self.world.agents.get(self.selected);x,y=self.body.topleft
        if a is None:self.label('Individual unavailable',x,y);return
        lines=['INHERITED TRAITS • actual values']+[f'{k.title()}: {v}' for k,v in a.traits.items()]
        lines+=['LEARNED MOVEMENT ASSOCIATIONS']+[f'{k[5:]}: {v:+d}' for k,v in sorted(a.learned.items()) if k.startswith('move:')]
        lines+=['RECENT EPISODES • latest three']+[f't{m.tick} {m.action}: {m.feature} {m.reward:+d}' for m in a.memories[-3:]]
        lines+=['OUTGOING RELATIONSHIP VALUES']+[f'#{i}: {v:+d}' for i,v in sorted(a.relationships.items(),key=lambda p:(-p[1],p[0]))[:5]]
        lines+=['Health max 100; can finish below zero.','Hunger/thirst >100 cause biological damage.','Fatigue cap 130; sleep is conditional at 65.','Cosmetic appearance implies no sex or role.']
        capacity=max(1,self.body.h//23);self.detail_offset=min(self.detail_offset,max(0,len(lines)-capacity))
        for line in lines[self.detail_offset:self.detail_offset+capacity]:
            y=self.paragraph(line,x,y,self.body.w,MUTED if line.isupper() else INK)+3

    def draw_personal(self):
        self.life.select(self.selected);self.life.update();a=life_summary(self.world,self.selected);x,y=self.body.topleft
        if a is None:self.label('Individual record unavailable',x,y);return
        self.label(f"{a['name']} • {a['status']}",x,y,GOLD);y+=25
        self.button(pygame.Rect(x,y,self.body.w,28),'Stop Watch W' if self.watch_id==self.selected else 'Watch life W','watch')
        y+=40
        if self.tab=='family':
            family=self.life.family(self.family_start,self.family_capacity)
            self.label('PARENTS',x,y,MUTED);y+=24
            for m in family['parents']:y=self.family_item(m,x,y)
            if not family['parents']:self.label('None recorded (founder)',x,y);y+=30
            self.label(f"CHILDREN • {self.family_start}..{min(len(self.life.children),self.family_start+self.family_capacity)} of {family['total_children']}",x,y+8,MUTED);y+=34
            for m in family['children']:y=self.family_item(m,x,y)
            if not family['children']:self.label('No child records on this page.',x,y)
        else:
            self.label(f'{len(self.life.positions)} objective events • chronological',x,y,MUTED);y+=27
            start=max(0,len(self.life.positions)-self.life_capacity) if self.life_tail else self.life_start
            for _,event in self.life.page(start,self.life_capacity):
                self.label(f'Tick {event.tick}',x,y,GOLD)
                self.paragraph(life_event_text(event,self.selected),x,y+19,self.body.w);y+=57
            if not self.life.positions:self.label('No eligible recorded events.',x,y)

    def family_item(self,m,x,y):
        rect=pygame.Rect(x,y,self.body.w,44)
        pygame.draw.rect(self.screen,(42,58,65),rect,border_radius=4)
        self.label(f"#{m['id']:05d} • {m['status']}",x+7,y+4,TEAL)
        born=f"Born tick {m['born']}" if m['born'] is not None else 'Birth unavailable'
        end=f" • died {m['died']}" if m['died'] is not None else ''
        self.label(born+end,x+7,y+23,MUTED)
        self.ui_hits.append((rect.clip(self.body),f"member:{m['id']}"));return y+50

    def draw_land(self):
        x,y=self.body.topleft;xy=self.tile_xy;c=self.world.cell(*xy);history=self.presentation.land.by_tile.get(xy,[])
        self.label(f'LAND • {xy}',x,y,GOLD,self.font);y+=30
        self.label(f'{c.terrain.title()} • food {c.food}/100',x,y);y+=28
        y=self.paragraph('Click a tile in Land mode. Player view; not a claim of gnome knowledge.',x,y,self.body.w,MUTED)+12
        self.label(f'{len(history)} recorded divine transitions',x,y,TEAL);y+=28
        start=max(0,len(history)-self.tile_capacity) if self.tile_tail else self.tile_start
        for p,change in self.presentation.land.page(xy,start,self.tile_capacity):
            self.label(f'Tick {p.completed_tick} • #{p.id} {p.kind.title()}',x,y,self.colors[p.kind])
            self.label(f"{change['before_terrain']} → {change['after_terrain']}",x,y+20);y+=58
        if not history:self.paragraph('No divine terrain transition recorded here. Natural terrain has no footprint badge.',x,y,self.body.w,MUTED)

    def draw_ledger(self):
        x,y=self.body.topleft;end=max(0,len(self.presentation.powers)-self.power_offset)
        self.label('DIVINE RECORDS • scroll for older',x,y,GOLD);y+=28
        cards=list(reversed(self.presentation.powers[max(0,end-self.power_capacity):end]))
        for p in cards:
            self.label(f"#{p['id']} {p['kind'].title()} • {p['status']}",x,y,self.colors[p['kind']]);y+=24
            self.label(f"{p['location']} • radius {p['radius']} • starts {p['activation']}",x,y);y+=23
            if p['terrain']:
                self.label(f"Actual changes {p['changed_cells']} • food removed {p['food_removed']}",x,y);y+=23
                y=self.paragraph('One-shot terrain action; no direct healing or injury.',x,y,self.body.w,MUTED)
            else:
                self.label(f"Expires {p['expires']} • {p['future_active_ticks']} ticks ahead",x,y);y+=23
                t=p['totals'];self.label(f"Regenerated {t['regenerated']} • normal {t['normal_regeneration']}",x,y);y+=23
                self.label(f"Delta {t['delta']:+d} • overridden pulses {t['overridden_cells']}",x,y);y+=23
                if p['overlap']:self.label('Coverage: '+p['overlap'],x,y,GOLD);y+=23
            y+=16
        if not cards:self.paragraph('No divine actions recorded. Select a power explicitly, then target the map.',x,y,self.body.w)

    def draw_statistics(self):
        x,y=self.body.topleft;s=self.presentation.status
        for title,value in [('Tick',s['tick']),('Living population',s['living']),('Births after 60 founders',s['born']-60),
                            ('Total deaths',s['deaths']),('Net change from 60',s['net_population_change']),
                            ('Food on map',s['food_stock']),('Active powers',s['active']),('Last assigned slots',str(sum(i is not None for i in self.world.slots))+'/60'),('Retained individuals',s['born'])]:
            self.label(title,x,y,MUTED);self.label(str(value),x+210,y,INK);y+=33
        y=self.paragraph('Terrain: grass • forest • rock • water • fractured hazard. Corner badges mark divine terrain history (H). Food bars are optional (B).',x,y+12,self.body.w)
        self.paragraph('No prosperity, beliefs or motives are inferred from these counts.',x,y+10,self.body.w,MUTED)

    def draw_advisor_new(self):
        x,y=self.body.topleft
        self.label('THE ADVISOR',x,y,GOLD,self.font)
        self.label('Facts sampled when you select a topic',x,y+30,MUTED)
        choices=self.advisor.choices()
        lines=wrap(self.small,self.advisor.text,self.body.w)
        choice_y=min(self.body.bottom-len(choices)*34,y+78+len(lines)*20)
        capacity=max(1,(choice_y-y-88)//20)
        self.advisor_scroll=min(self.advisor_scroll,max(0,len(lines)-capacity))
        for j,line in enumerate(lines[self.advisor_scroll:self.advisor_scroll+capacity]):self.label(line,x,y+58+j*20)
        if len(lines)>capacity:self.label('Wheel over reply to read more',x,choice_y-25,MUTED)
        for choice,label in choices:
            self.button(pygame.Rect(x,choice_y,self.body.w,29),choice+'. '+label,'advisor:'+choice);choice_y+=34

    def draw_feed(self):
        if not self.feed_mode:self.feed_hits=[];return
        r=self.event_rect;pygame.draw.rect(self.screen,PANEL,r,border_radius=6)
        self.label('WORLD HAPPENINGS',r.x+10,r.y+7,GOLD)
        self.button(self.feed_button,'Compact' if self.feed_mode==2 else 'History','feed')
        self.feed_hits=[];self.screen.set_clip(r)
        for j,(_,event) in enumerate(self.presentation.events.page(self.event_offset,self.event_capacity)):
            y=r.y+35+j*36;color=self.colors.get(event.detail.get('power'),TEAL) if event.kind.startswith('divine_') else GOLD if event.kind=='death' else MUTED
            self.label(f't{event.tick}',r.x+10,y,color)
            line=happening(event,self.world);lines=wrap(self.small,line,r.w-100)
            for k,text in enumerate(lines[:2]):self.label(text,r.x+80,y+k*16,INK)
            self.feed_hits.append((pygame.Rect(r.x,y,r.w,35),event))
        self.screen.set_clip(None)

    def draw(self):
        self.sync();self.hover=self.map_target(self.pointer);self.ui_hits=[]
        self.screen.fill(BG);s=self.presentation.status;w=self.screen.get_width();h=self.screen.get_height()
        self.label('GNOME FORTRESS',14,12,GOLD,self.font)
        state='EXTINCT' if self.world.extinct else 'PAUSED' if self.paused else 'RUNNING'
        if self.saving or getattr(self,'checkpoint_pending',False):state+=' • SAVING'
        if getattr(self,'save_error',False):state+=' • UNSAVED'
        self.label(state,max(245,self.font.size('GNOME FORTRESS')[0]+35),14,TEAL if not self.paused else GOLD)
        self.label(f"Tick {s['tick']} • {s['living']} living • {s['born']-60} births • {s['deaths']} deaths",14,39)
        camera_status=f'Follow #{self.follow_id:05d}' if self.follow_id is not None else 'Free camera'
        if w<1100:self.label(f'{self.speeds[self.speed_index]} t/s • '+camera_status,w-220,14,MUTED)
        else:self.label(f'{self.speeds[self.speed_index]} ticks/s • '+camera_status,max(520,self.small.size(f"Tick {s['tick']} • {s['living']} living • {s['born']-60} births • {s['deaths']} deaths")[0]+35),39,MUTED)
        if w>=1200:
            lx=w-390
            for kind in ('grass','forest','rock','water','hazard'):
                self.screen.blit(terrain_tile(kind,0,16),(lx,15))
                image=text_image(18,kind.title(),MUTED);self.screen.blit(image,(lx+20,15));lx+=image.get_width()+31
        for name,(rect,label) in self.toolbar.items():
            active=(name=='observe' and self.mode is None and not self.tile_select) or name==self.mode or (name=='food' and self.food_overlay)
            self.button(rect,label,name,active)
        self.draw_world();self.draw_feed()
        if self.inspector_open:
            pygame.draw.rect(self.screen,PANEL,self.panel_rect,border_radius=6)
            for name,(rect,label) in self.tabs.items():self.button(rect,label,'tab:'+name,self.tab==name and not self.advisor.open)
            self.screen.set_clip(self.body)
            if self.advisor.open:self.draw_advisor_new()
            elif self.tab=='gnome':self.draw_card()
            elif self.tab=='details':self.draw_details()
            elif self.tab in ('life','family'):self.draw_personal()
            elif self.tab=='terrain':self.draw_land()
            elif self.tab=='powers':self.draw_ledger()
            else:self.draw_statistics()
            self.screen.set_clip(None)
        if self.world.extinct:
            rect=pygame.Rect(self.viewport.x+20,self.viewport.y+40,min(self.viewport.w-40,520),205)
            pygame.draw.rect(self.screen,BG,rect,border_radius=9);pygame.draw.rect(self.screen,GOLD,rect,2,border_radius=9)
            lines=['THE WORLD HAS FALLEN SILENT',f'Final tick {self.world.extinct_tick} • population 0',
                   f'Total born {len(self.world.agents)} • deaths {len(self.world.agents)}',f'Divine interventions {len(self.world.interventions)}',
                   'This timeline has ended. Inspection remains.', 'Esc saves and exits.']
            for j,line in enumerate(lines):self.label(line,rect.x+14,rect.y+16+j*28,GOLD if j==0 else INK)
        # Controls are always visible; long operational notices stay in a clipped line.
        self.screen.set_clip(pygame.Rect(10,h-27,w-20,26))
        hint=(self.notice if self.mode else self.follow_note) or (self.notice if self.notice and (time.monotonic()<self.notice_until or getattr(self,'save_error',False) or self.notice.startswith('Saving')) else f'Wheel zoom • arrows pan • C follow • W Watch • Home fit • V happenings • B food • H footprints • Esc save & exit')
        self.label(hint,12,h-24,GOLD if self.mode else MUTED);self.screen.set_clip(None)
        pygame.display.flip()
