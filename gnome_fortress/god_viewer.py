"""G2 God interface: disposable presentation over authoritative G1 state."""
from pathlib import Path
import os
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import pygame

from .game import DEFAULT_DURATION, DEFAULT_RADIUS
from .game_presentation import WorldPresentation, agent_view, event_text
from .runtime import CheckpointWorker
from .viewer import Observer

POWER_COLORS={'rain':(93,174,230),'drought':(230,166,76)}
INK=(219,228,225)
MUTED=(158,176,180)
GOLD=(247,213,131)


def wrap(font,text,width):
    lines=[];line=''
    for word in text.split():
        candidate=(line+' '+word).strip()
        if line and font.size(candidate)[0]>width:lines.append(line);line=word
        else:line=candidate
    return lines+[line] if line else lines


class GodObserver(Observer):
    def __init__(self,world,rate=None,paused=False):
        super().__init__(world,rate,paused)
        desktop=pygame.display.get_desktop_sizes()[0]
        height=max(600,min(820,desktop[1]-70));panel_width=470
        target_width=max(900,min(1340,desktop[0]-40))
        self.tile=max(8,min(18,(target_width-panel_width)//world.width,
                            (height-max(160,height//4)-12)//world.height))
        self.map_width=world.width*self.tile
        self.screen=pygame.display.set_mode((self.map_width+panel_width,height))
        pygame.display.set_caption('Gnome Fortress | The Living World')
        self.mode=None;self.hover=None;self.pointer=(0,0)
        self.notice='R / D to target. O to observe. Powers act next tick.'
        self.last_request=world.interventions[-1].id if world.interventions else None
        if self.last_request:self.notice=''
        self.presentation=WorldPresentation(world)
        self.event_offset=0;self.power_offset=0;self.tab='gnome'
        self.event_rect=pygame.Rect(0,world.height*self.tile+8,self.map_width,height-world.height*self.tile-8)
        self.event_rows=[]
        self.buttons={name:pygame.Rect(self.map_width+12+i*149,124,142,32)
                      for i,name in enumerate(('observe','rain','drought'))}
        self.tabs={name:pygame.Rect(self.map_width+12+i*223,250,216,28)
                   for i,name in enumerate(('gnome','powers'))}

    @property
    def event_capacity(self):return max(1,(self.event_rect.height-48)//36)

    @property
    def power_capacity(self):return max(1,(self.screen.get_height()-330)//108)

    def sync(self):
        added=self.presentation.refresh()
        if self.event_offset:self.event_offset+=added
        self.event_offset=min(self.event_offset,max(0,len(self.presentation.events.positions)-self.event_capacity))
        self.power_offset=min(self.power_offset,max(0,len(self.world.interventions)-self.power_capacity))

    def map_target(self,pos):
        x,y=pos
        return (x//self.tile,y//self.tile) if 0<=x<self.map_width and 0<=y<self.world.height*self.tile else None

    def browse_events(self,amount):
        self.event_offset=max(0,min(self.event_offset+amount,
            max(0,len(self.presentation.events.positions)-self.event_capacity)))

    def handle(self,events):
        self.sync()
        for event in events:
            if event.type==pygame.MOUSEMOTION:
                self.pointer=event.pos;self.hover=self.map_target(event.pos)
            elif event.type==pygame.MOUSEWHEEL:
                pos=getattr(event,'pos',self.pointer)
                if self.event_rect.collidepoint(pos):self.browse_events(event.y*3)
                elif pos[0]>=self.map_width and pos[1]>=280 and self.tab=='powers':
                    self.power_offset=max(0,min(self.power_offset+event.y,
                        max(0,len(self.world.interventions)-self.power_capacity)))
            elif event.type==pygame.KEYDOWN and event.key in (pygame.K_PAGEUP,pygame.K_PAGEDOWN,pygame.K_END):
                if event.key==pygame.K_END:self.event_offset=0
                else:self.browse_events(self.event_capacity*(1 if event.key==pygame.K_PAGEUP else -1))
            elif event.type==pygame.KEYDOWN and event.key in (pygame.K_F1,pygame.K_F2):
                self.tab='gnome' if event.key==pygame.K_F1 else 'powers'
            elif event.type==pygame.KEYDOWN and event.key in (pygame.K_r,pygame.K_d,pygame.K_o):
                self.mode={pygame.K_r:'rain',pygame.K_d:'drought',pygame.K_o:None}[event.key]
            elif event.type==pygame.MOUSEBUTTONDOWN:
                self.pointer=event.pos;self.hover=self.map_target(event.pos)
                if event.button==3:self.mode=None
                elif event.button==1:
                    button=next((name for name,r in self.buttons.items() if r.collidepoint(event.pos)),None)
                    tab=next((name for name,r in self.tabs.items() if r.collidepoint(event.pos)),None)
                    if button:self.mode=None if button=='observe' else button
                    elif tab:self.tab=tab
                    elif self.event_rect.collidepoint(event.pos):
                        identity=next((identity for r,identity in self.event_rows if r.collidepoint(event.pos)),None)
                        if identity in self.world.agents:self.selected=identity;self.tab='gnome'
                    elif self.hover and self.mode:
                        if self.saving:self.notice='Saving: wait for completion before casting.'
                        elif self.world.extinct:self.notice='This world has ended.'
                        else:
                            p=self.world.request(self.mode,*self.hover)
                            self.last_request=p.id;self.notice='';self.tab='powers';self.power_offset=0
                    elif self.hover:
                        super().handle([event]);self.tab='gnome'
            else:
                super().handle([event])
                if event.type==pygame.KEYDOWN and event.key==pygame.K_TAB:self.tab='gnome'

    def advance(self,seconds):
        if self.world.extinct:
            self.paused=True;self.accumulator=0;self.single_step=False
            return
        super().advance(seconds)
        if self.world.extinct:self.paused=True;self.accumulator=0

    def region(self,kind,x,y,radius,preview=False):
        color=POWER_COLORS[kind]
        layer=pygame.Surface((self.map_width,self.world.height*self.tile),pygame.SRCALPHA)
        for cy in range(max(0,y-radius),min(self.world.height,y+radius+1)):
            for cx in range(max(0,x-radius),min(self.world.width,x+radius+1)):
                if (cx-x)**2+(cy-y)**2<=radius**2:
                    rect=(cx*self.tile,cy*self.tile,self.tile-1,self.tile-1)
                    pygame.draw.rect(layer,(*color,50 if preview else 30),rect)
                    pygame.draw.rect(layer,(*color,175 if preview else 65),rect,1)
        self.screen.blit(layer,(0,0))

    def notice_text(self):
        if self.notice:return self.notice
        if self.last_request:
            p=self.world.interventions[self.last_request-1]
            return f'#{p.id} {p.kind.title()}: {p.status} | starts {p.activation_tick}, expires {p.expires_tick}'
        return 'Observe freely; no divine power selected.'

    def label(self,text,x,y,color=INK,font=None):
        self.screen.blit((font or self.small).render(text,True,color),(x,y))

    def markers(self):
        for a in self.world._living_agents.values():
            cx=a.x*self.tile+self.tile//2;cy=a.y*self.tile+self.tile//2
            if a.sleep_until>self.world.tick:
                pygame.draw.rect(self.screen,(121,164,210),(cx-3,cy,7,3))
                self.label('z',cx+2,cy-10,(180,209,242))
            else:
                pygame.draw.rect(self.screen,(235,203,131),(cx-2,cy-1,5,5))
                pygame.draw.polygon(self.screen,(194,91,69),[(cx-4,cy-2),(cx+4,cy-2),(cx,cy-7)])
        a=self.world.agents.get(self.selected)
        if a:
            cx=a.x*self.tile+self.tile//2;cy=a.y*self.tile+self.tile//2
            pygame.draw.rect(self.screen,(12,19,24),(cx-8,cy-9,17,18),3)
            pygame.draw.rect(self.screen,GOLD,(cx-8,cy-9,17,18),1)
            text=f'#{a.id}'
            image=self.small.render(text,True,GOLD)
            x=max(0,min(self.map_width-image.get_width()-6,cx+9));y=max(0,cy-22)
            pygame.draw.rect(self.screen,(19,27,32),(x,y,image.get_width()+6,17))
            self.screen.blit(image,(x+3,y+1))

    def draw_event_feed(self):
        rect=self.event_rect
        pygame.draw.rect(self.screen,(24,33,39),rect)
        self.label('RECORDED EVENTS',12,rect.y+8,GOLD)
        total=len(self.presentation.events.positions)
        self.label(f'{total} indexed | PgUp/PgDn, wheel | End: latest',190,rect.y+8,MUTED)
        self.event_rows=[]
        for j,(sequence,event) in enumerate(self.presentation.events.page(self.event_offset,self.event_capacity)):
            y=rect.y+33+j*36
            self.label(f't{event.tick}',12,y,POWER_COLORS['rain'] if event.kind.startswith('divine_') else GOLD)
            lines=wrap(self.small,event_text(event,self.world),self.map_width-90)
            for i,line in enumerate(lines[:2]):self.label(line,80,y+i*15)
            self.event_rows.append((pygame.Rect(0,y,self.map_width,34),event.actor))
        if self.event_offset:self.label(f'Browsing older events (+{self.event_offset} from latest)',12,self.screen.get_height()-16,MUTED)

    def draw_individual(self,x,y):
        a=agent_view(self.world,self.selected)
        if not a:self.label('Individual unavailable',x,y);return
        status=a['status']+(f": {a['death_cause']}" if a['status']=='deceased' else '')
        lines=[(a['name']+' | '+status,GOLD),
            (f"Age {a['age']} | recorded action: {a['action']}",INK),
            (f"Health {a['health']} | hunger {a['hunger']} | thirst {a['thirst']}",INK),
            (f"Fatigue {a['fatigue']} | location {a['location']}",INK),
            (f"Parents: {', '.join(map(str,a['parents'])) or 'none (founder)'} | children {a['children']}",INK),
            ('Inherited traits (actual values):',MUTED)]
        traits=list(a['traits'].items())
        for start in (0,3):lines.append((', '.join(f'{k[:3]}={v}' for k,v in traits[start:start+3]),INK))
        lines.append(('Learned movement associations:',MUTED))
        if a['movement']:
            lines.extend((f"  {key[5:]}: {value:+d}",INK) for key,value in a['movement'].items())
        else:lines.append(('  none recorded',INK))
        lines.append(('Recent recorded episodes (latest three):',MUTED))
        if a['memories']:
            lines.extend((f'  t{tick}: {action} {feature} {reward:+d}',INK) for tick,action,feature,reward in a['memories'])
        else:lines.append(('  none recorded',INK))
        for i,(line,color) in enumerate(lines):self.label(line,x,y+i*18,color)

    def draw_powers(self,x,y):
        cards=self.presentation.powers
        end=max(0,len(cards)-self.power_offset)
        visible=reversed(cards[max(0,end-self.power_capacity):end])
        if not cards:self.label('No interventions recorded. R / D, then click map.',x,y,MUTED)
        for j,p in enumerate(visible):
            top=y+j*108
            pygame.draw.rect(self.screen,(29,39,46),(x-3,top-4,446,100),border_radius=5)
            status=p['status']+(f" / {p['overlap']}" if p['overlap'] else '')
            self.label(f"#{p['id']} {p['kind'].title()} | {status}",x+5,top,POWER_COLORS[p['kind']])
            self.label(f"{p['location']}  radius {p['radius']} | {p['future_active_ticks']} active ticks ahead",x+5,top+19)
            self.label(f"Active window {p['activation']}..{p['expires']-1}; expires {p['expires']}",x+5,top+37,MUTED)
            t=p['totals']
            self.label(f"Food regenerated {t['regenerated']:+d} | ordinary {t['normal_regeneration']:+d}",x+5,top+55)
            self.label(f"Delta {t['delta']:+d} | overridden cell-pulses {t['overridden_cells']}",x+5,top+73)
        self.label('Delta: regeneration vs ordinary pulses on same stocks.',x,self.screen.get_height()-35,MUTED)
        self.label(f'{len(cards)} records | wheel here: older/newer powers',x,self.screen.get_height()-18,MUTED)

    def draw(self):
        self.sync()
        super().draw(present=False)
        w=self.world;s=self.presentation.status;x=self.map_width+12
        layer=pygame.Surface((self.map_width,w.height*self.tile),pygame.SRCALPHA)
        for (cx,cy),kind in self.presentation.region_cells.items():
            color=POWER_COLORS[kind];rect=(cx*self.tile,cy*self.tile,self.tile-1,self.tile-1)
            pygame.draw.rect(layer,(*color,55),rect)
            pygame.draw.rect(layer,(*color,110),rect,1)
        self.screen.blit(layer,(0,0))
        if self.mode and self.hover and not w.extinct:self.region(self.mode,*self.hover,DEFAULT_RADIUS,preview=True)
        self.markers()
        pygame.draw.rect(self.screen,(19,27,33),(self.map_width,0,470,self.screen.get_height()))
        self.label('GNOME FORTRESS | THE LIVING WORLD',x,12,GOLD,self.font)
        state='SAVING' if self.saving else 'EXTINCT' if w.extinct else 'PAUSED' if self.paused else 'RUNNING'
        self.label(f"Tick {s['tick']} | seed {w.seed} | {state} | target {self.speeds[self.speed_index]} t/s",x,36)
        self.label(f"Living {s['living']} | net {s['net_population_change']:+d} since 60 founders",x,56)
        self.label(f"Born total {s['born']} (includes founders) | deaths {s['deaths']}",x,76)
        self.label(f"Food on map {s['food_stock']:,} units | active powers {s['active']}",x,96)
        for name,rect in self.buttons.items():
            selected=(name=='observe' and self.mode is None) or self.mode==name
            pygame.draw.rect(self.screen,(57,86,96) if selected else (33,45,53),rect,border_radius=5)
            self.label(name.title(),rect.x+16,rect.y+8,GOLD if selected else INK,self.font)
        self.label(f"{self.mode.title() if self.mode else 'Observe / inspect'} | radius {DEFAULT_RADIUS} | duration {DEFAULT_DURATION} ticks",x,165)
        self.label('R/D select | click cast | O/right-click observe',x,185,MUTED)
        self.label('Space pause | +/- speed | . step | S save | Esc exit',x,204,MUTED)
        self.label(self.notice_text(),x,226,GOLD)
        for name,rect in self.tabs.items():
            pygame.draw.rect(self.screen,(46,63,72) if self.tab==name else (28,39,46),rect,border_radius=4)
            self.label('Gnome [F1]' if name=='gnome' else 'Interventions [F2]',rect.x+12,rect.y+6)
        if self.tab=='gnome':
            self.draw_individual(x,292)
            if self.screen.get_height()>=680:
                self.label('Hat: awake | blue z: sleeping | gold frame: selected',x,self.screen.get_height()-35,MUTED)
        else:self.draw_powers(x,292)
        clip=self.screen.get_clip()
        self.screen.set_clip(self.event_rect)
        self.draw_event_feed()
        self.screen.set_clip(clip)
        if w.extinct:
            rect=pygame.Rect(24,80,max(400,self.map_width-48),245)
            pygame.draw.rect(self.screen,(24,29,35),rect,border_radius=12)
            pygame.draw.rect(self.screen,GOLD,rect,2,border_radius=12)
            lines=['THE WORLD HAS FALLEN SILENT',f'Final tick: {w.extinct_tick}',
                   f'Total individuals born: {len(w.agents)} (founders included)',
                   f'Total deaths: {sum(not a.alive for a in w.agents.values())}',
                   f'Divine interventions used: {len(w.interventions)}','Final population: 0',
                   'This run has ended. Esc saves and exits.']
            for i,line in enumerate(lines):self.label(line,rect.x+20,rect.y+20+i*29,INK,self.font)
        pygame.display.flip()

def run(world,path,save_callback,checkpoint_ticks=300,max_frames=None,stop_requested=lambda:False,
        rate=None,paused=False,capture=None):
    observer=GodObserver(world,rate,paused);clock=pygame.time.Clock()
    worker=CheckpointWorker(save_callback);last_save=world.tick;frames=0;dirty=True
    try:
        while observer.running and not stop_requested() and (max_frames is None or frames<max_frames):
            seconds=clock.tick(15 if observer.paused or worker.pending or world.extinct else 60)/1000
            observer.saving=worker.pending
            events=pygame.event.get();observer.handle(events)
            if not observer.running:break
            if worker.pending and worker.future.done():
                try:
                    metrics=worker.poll();observer.notice=f"Saved tick {metrics['tick']}"
                    last_save=world.tick
                except Exception as error:
                    observer.notice=f'Save failed: {type(error).__name__}; see terminal'
                    print(f'Gameplay save failed: {error}',flush=True)
                    observer.paused=True
                observer.saving=False;seconds=0;dirty=True
            observer.advance(seconds)
            if not worker.pending and (observer.save_requested or world.tick-last_save>=checkpoint_ticks):
                worker.start(world,path);observer.saving=True;observer.save_requested=False;dirty=True
            if dirty or events or (not observer.paused and not observer.saving):
                observer.draw();dirty=False
            frames+=1
    finally:
        try:
            worker.close()
            if capture:
                observer.draw();Path(capture).parent.mkdir(parents=True,exist_ok=True)
                pygame.image.save(observer.screen,str(capture))
        finally:pygame.quit()
