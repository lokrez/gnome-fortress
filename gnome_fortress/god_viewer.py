"""Small God interface on the existing observer; wall clocks only pace complete ticks."""
from pathlib import Path
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

from .game import DEFAULT_DURATION, DEFAULT_RADIUS
from .runtime import CheckpointWorker
from .viewer import Observer

POWER_COLORS={'rain':(93,174,230),'drought':(230,166,76)}


class GodObserver(Observer):
    def __init__(self,world,rate=None,paused=False):
        super().__init__(world,rate,paused)
        pygame.display.set_caption('Gnome Fortress | The First Miracle')
        self.mode=None
        self.hover=None
        self.notice='Observe freely. R: Rain | D: Drought | O: Observe'
        self.buttons={name:pygame.Rect(self.map_width+12+i*120,110,114,33)
                      for i,name in enumerate(('observe','rain','drought'))}

    def map_target(self,pos):
        x,y=pos
        return (x//self.tile,y//self.tile) if 0<=x<self.map_width and 0<=y<self.world.height*self.tile else None

    def handle(self,events):
        for event in events:
            if event.type==pygame.MOUSEMOTION:
                self.hover=self.map_target(event.pos)
            elif event.type==pygame.KEYDOWN and event.key in (pygame.K_r,pygame.K_d,pygame.K_o):
                self.mode={pygame.K_r:'rain',pygame.K_d:'drought',pygame.K_o:None}[event.key]
            elif event.type==pygame.MOUSEBUTTONDOWN:
                self.hover=self.map_target(event.pos)
                if event.button==3:
                    self.mode=None
                elif event.button==1:
                    button=next((name for name,rect in self.buttons.items() if rect.collidepoint(event.pos)),None)
                    if button:
                        self.mode=None if button=='observe' else button
                    elif self.hover and self.mode:
                        if self.saving:self.notice='Saving: wait for completion before casting.'
                        elif self.world.extinct:self.notice='This world has ended.'
                        else:
                            p=self.world.request(self.mode,*self.hover)
                            self.notice=f'Requested #{p.id} {p.kind.title()} for tick {p.activation_tick}'
                    elif self.hover:
                        super().handle([event])
            else:
                super().handle([event])

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
                    pygame.draw.rect(layer,(*color,55 if preview else 35),rect)
                    if preview:pygame.draw.rect(layer,(*color,170),rect,1)
        self.screen.blit(layer,(0,0))

    def draw(self):
        # Reuse the complete existing map, gnomes, food bars and selection rendering.
        super().draw(present=False)
        w=self.world
        for p in sorted(w.interventions,key=lambda p:(p.kind=='drought',p.id)):
            if p.status=='active':self.region(p.kind,p.x,p.y,p.radius)
        if self.mode and self.hover and not w.extinct:
            self.region(self.mode,*self.hover,DEFAULT_RADIUS,preview=True)
        panel=pygame.Rect(self.map_width,0,390,self.screen.get_height())
        pygame.draw.rect(self.screen,(19,24,29),panel)
        def text(line,y,color=(218,225,224)):
            self.screen.blit(self.small.render(line,True,color),(self.map_width+12,y))
        text('GNOME FORTRESS | THE FIRST MIRACLE',14)
        text(f'Seed {w.seed}   Tick {w.tick}   Living {len(w._living_agents)}',36)
        text(f"{'SAVING' if self.saving else 'EXTINCT' if w.extinct else 'PAUSED' if self.paused else 'RUNNING'} | {self.speeds[self.speed_index]} target t/s | Born {len(w.agents)}",56)
        text('Space pause | +/- speed | . step | S save',78)
        for name,rect in self.buttons.items():
            selected=(name=='observe' and self.mode is None) or self.mode==name
            pygame.draw.rect(self.screen,(57,86,96) if selected else (36,44,51),rect,border_radius=5)
            self.screen.blit(self.font.render(name.title(),True,(234,232,218)),(rect.x+15,rect.y+8))
        text(f"Selected: {self.mode.title() if self.mode else 'Observation / gnome inspection'}",157)
        text(f'Radius {DEFAULT_RADIUS} tiles | duration {DEFAULT_DURATION} ticks',177)
        text('Rain: 2x growth | Drought: growth suppressed',197)
        text('Drought wins overlaps. Rain does not stack.',217)
        text('Click map to cast | O / right-click to observe',237)
        text('Acts next tick; paused requests wait for a step.',257)
        text(self.notice,282,(237,206,134))
        text('Intervention history (latest four):',310)
        for i,p in enumerate(w.interventions[-4:]):
            text(f'#{p.id} {p.kind} ({p.x},{p.y}) {p.status} t{p.activation_tick}..{p.expires_tick-1}',331+i*18,POWER_COLORS[p.kind])
        a=w.agents.get(self.selected)
        if a:
            text(f"{a.name} | {'alive' if a.alive else a.death_cause}",418)
            text(f'Age {a.age} | {a.action} | children {a.children}',438)
            text(f'Health {a.health} | hunger {a.hunger} | thirst {a.thirst}',458)
            text(f'Fatigue {a.fatigue} | position ({a.x},{a.y})',478)
            text('Inherited: '+', '.join(f'{k[:3]}={v}' for k,v in list(a.traits.items())[:3]),498)
            text('                '+', '.join(f'{k[:3]}={v}' for k,v in list(a.traits.items())[3:]),518)
            text('Movement: '+(', '.join(f'{k[5:]}={v}' for k,v in sorted(a.learned.items()) if k.startswith('move:')) or 'none'),538)
        text('Green bars = food | blue = water | red = hazard',578)
        text('Blue haze = Rain | amber haze = Drought',598)
        text('Esc / close: save and exit. Resume on launch.',622)
        if w.extinct:
            rect=pygame.Rect(50,110,max(400,self.map_width-100),245)
            pygame.draw.rect(self.screen,(24,29,35),rect,border_radius=12)
            pygame.draw.rect(self.screen,(192,151,108),rect,2,border_radius=12)
            lines=['THE WORLD HAS FALLEN SILENT',f'Final tick: {w.extinct_tick}',
                   f'Total individuals born: {len(w.agents)} (founders included)',
                   f'Total deaths: {sum(not a.alive for a in w.agents.values())}',
                   f'Divine interventions used: {len(w.interventions)}','Final population: 0',
                   'This run has ended. Esc saves and exits.']
            for i,line in enumerate(lines):
                self.screen.blit(self.font.render(line,True,(230,220,202)),(rect.x+20,rect.y+20+i*29))
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
