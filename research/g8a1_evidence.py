"""Actual Pygame folklore assets/captures and bounded isolated-world measurements.

No player checkpoint is read. Natural histories are generated from seed 1.
Environmental demonstrations use explicitly recorded divine requests.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import tempfile
import time
import types
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker,capture_snapshot
from gnome_fortress.game_session import game_session
from gnome_fortress.god_viewer import run
from gnome_fortress import pixel_art as art

BASELINE='2636861062eb8762c55335943379613ed457a5b1'


def measure(fn,count=30):
    values=[]
    for _ in range(count):
        start=time.perf_counter();fn();values.append((time.perf_counter()-start)*1000)
    ordered=sorted(values)
    return dict(samples=count,median_ms=statistics.median(values),p95_ms=ordered[int((count-1)*.95)],max_ms=max(values))


def baseline_observer():
    """Run exactly the two accepted art/view source files, no working-tree writes."""
    for file,name in [('pixel_art','_g8a_reference_art'),('living_viewer','_g8a_reference_view')]:
        source=subprocess.check_output(['git','show',f'{BASELINE}:gnome_fortress/{file}.py'],text=True)
        if file=='living_viewer':source=source.replace('from .pixel_art import','from ._g8a_reference_art import')
        module=types.ModuleType('gnome_fortress.'+name);module.__package__='gnome_fortress'
        sys.modules[module.__name__]=module;exec(compile(source,f'<{BASELINE}/{file}.py>','exec'),module.__dict__)
    return module.LivingObserver


def art_sheet(root):
    pygame.init();s=pygame.Surface((1400,1110));s.fill(art.PARCHMENT)
    def title(text,x,y):s.blit(pygame.font.Font(None,25).render(text,True,art.INK),(x,y))
    title('GNOME FORTRESS / MACABRE GARDEN FOLKLORE / ORIGINAL NATIVE ASSETS',25,14)
    title('Eight silhouettes / identity cosmetics, no classes or hat genetics',25,46)
    for i in range(8):
        x=30+i*169;im=pygame.transform.scale(art.gnome_native(art.appearance(i)),(96,120));s.blit(im,(x,80))
        # Pure black silhouette shows that variety goes beyond recoloring.
        mask=pygame.mask.from_surface(art.gnome_native(art.appearance(i)))
        silhouette=mask.to_surface(setcolor=art.OUTLINE,unsetcolor=art.PARCHMENT)
        s.blit(pygame.transform.scale(silhouette,(64,80)),(x,213));title(str(i),x+23,299)
    title('States: awake / walk A / walk B / reclining sleep / archival death (not an undead agent)',25,340)
    for i,(sleep,phase) in enumerate(((False,0),(False,0),(False,1),(True,0))):
        s.blit(art.gnome_sprite(art.appearance(1),sleep,88,phase)[0],(35+i*150,380))
    s.blit(art.death_portrait(88),(650,380))
    title('Terrain / 32px native / upper-left light / decorative plants are not extra resources',25,490)
    for i,k in enumerate(art.TERRAIN_COLORS):
        s.blit(art.terrain_tile(k,2,96),(30+i*160,530));title(k,30+i*160,633)
    title('Recorded provenance: Rupture / Rewild / Wellspring',850,490)
    for i,(k,p) in enumerate((('hazard','rupture'),('forest','rewild'),('water','wellspring'))):
        x=850+i*170;s.blit(art.terrain_tile(k,1,96),(x,530));s.blit(art.terrain_decoration(k,(k,)*4,p,96),(x,530));title(p,x,633)
    title('Field journal / scripted Advisor / objective record glyphs',25,680)
    s.blit(art.journal_panel(620,160),(25,716))
    title('SPECIMEN RECORD / Gnome #00001',45,735)
    s.blit(art.gnome_sprite(art.appearance(1),False,92)[0],(50,768))
    title('Appearance is presentation. The world owns the facts.',140,788)
    for i,k in enumerate(('rain','drought','rupture','rewild','wellspring')):
        x=710+i*135;s.blit(art.icon(k,40),(x,735));title(k,x,788)
    for i,k in enumerate(('birth','death','hazard','divine')):
        s.blit(art.icon(k,24),(720+i*140,840));title(k,748+i*140,842)
    title('Same individual at overview / normal / close zoom (nearest-neighbor)',25,920)
    for x,h in ((40,12),(160,29),(320,86),(520,120)):
        s.blit(art.gnome_sprite(art.appearance(1),False,h)[0],(x,1075-h));title(str(h)+'px',x,1080)
    pygame.image.save(s,str(root/'art-sheet.png'));pygame.quit()


def captures(root):
    folder=root/'captures';folder.mkdir(parents=True,exist_ok=True);rows=[]
    w=TerrainWorld(1);v=LivingObserver(w,paused=True,window_size=(1280,720))
    def capture(name,view=v,note='Natural simulation; no biological events injected'):
        before=view.world.digest();view.draw();pygame.image.save(view.screen,str(folder/(name+'.png')))
        assert view.world.digest()==before
        rows.append(dict(name=name,tick=view.world.tick,population=len(view.world.living()),selected=view.selected,
                         camera_tile=view.camera.tile,window=list(view.screen.get_size()),note=note))
    capture('01-new-world')
    w.step(300);v.sync();v.camera.tile=96;v.camera.clamp()
    # Pick the most naturally occupied tile at this predeclared time, no relocation.
    xy=max(v.occupants,key=lambda p:(len(v.occupants[p]),-p[1],-p[0]));v.camera.center_tile(*xy)
    capture('02-natural-gnomes')
    v.select_individual(v.occupants[xy][0]);v.center_selected();capture('03-close-gnome');capture('04-field-journal-card')
    v.toggle_follow();v.paused=False
    for _ in range(20):w.step();v.draw()
    capture('05-camera-follow');v.paused=True;v.follow_id=None
    v.advisor.start();capture('06-advisor');v.advisor.open=False
    v.feed_mode=2;v.layout(v.screen.get_size());v.camera.fit();capture('07-world-happenings')
    # Actual deterministic gameplay requests; no scripted deaths or movement.
    target=next((x,y) for y in range(3,w.height-3) for x in range(3,w.width-3) if w.cell(x,y).terrain=='forest')
    v.feed_mode=1;v.layout(v.screen.get_size());v.camera.tile=64;v.camera.clamp();v.camera.center_tile(*target)
    v.set_mode('rupture');v.pointer=v.camera.tile_rect(*target).center;capture('08-divine-targeting',note='First interior forest tile (3-tile margin) for a visible footprint; ordinary targeting')
    w.request('rupture',*target);w.step();v.set_mode(None);v.sync();capture('09-ruptured-land',note='Recorded Rupture; no direct biological intervention')
    w.request('rewild',*target);w.step();v.sync();v.navigate('terrain');v.tile_xy=target;capture('10-rewilded-land-history',note='Recorded Rewild after Rupture; prior transitions retained')
    # Terrain coverage is an actual map crop, not rearranged tile art.
    v.camera.fit();v.navigate('gnome');capture('11-five-terrain-types')
    pygame.quit()
    for size,name in [((800,600),'12-800x600'),((1920,1080),'13-1920x1080'),((3840,2160),'14-4k-viewport')]:
        view=LivingObserver(w,paused=True,window_size=size)
        if size==(3840,2160) and os.environ.get('SDL_VIDEODRIVER')!='dummy':
            # Borderless evidence window avoids desktop titlebar work-area truncation.
            view.screen=pygame.display.set_mode(size,pygame.NOFRAME);view.layout(view.screen.get_size())
        capture(name,view);pygame.quit()
    save_rows=[]
    class DuringSave(LivingObserver):
        def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.save_requested=True;self.seen=0;self.start_tick=self.world.tick
        def handle(self,events):
            super().handle(events)
            if getattr(self,'checkpoint_pending',False):
                self.seen+=1;save_rows.append(dict(tick=self.world.tick,pending=True))
                if self.seen==12:
                    capture('15-background-save',self,'Real detached writer; world stepped during save')
                    self.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_ESCAPE)])
    with tempfile.TemporaryDirectory(prefix='g8a1-checkpoint-') as temporary:
        path=Path(temporary)/'evidence.g5.sqlite'
        with game_session(path):
            save_game(w,path);initial=w.tick
            run(w,path,slow_save,rate=60,max_frames=120,observer_class=DuringSave,worker_class=TerrainCheckpointWorker)
            # Explicit final save verifies the current continuation, not a fabricated autosave claim.
            save_game(w,path);loaded=load_game(path);assert loaded.state()==w.state()
            assert w.tick>initial
    art_sheet(root)
    result=dict(seed=1,driver=os.environ.get('SDL_VIDEODRIVER'),human_playtest=False,captures=rows,
                naturally_busiest_tile=xy,natural_occupants=len(v.occupants.get(xy,[])),environmental_target=target,
                final_digest=w.digest(),save_frames=save_rows,save_load_equal=True)
    (root/'evidence'/'captures.json').write_text(json.dumps(result,indent=2)+'\n')


def slow_save(world,path):time.sleep(.5);return save_game(world,path)


def cache_info():
    return {name:getattr(art,name).cache_info()._asdict() for name in ('gnome_native','gnome_sprite','terrain_native','terrain_tile','illustrated_tile','_terrain_decoration','icon','journal_panel')}


def benchmarks(root):
    reference=baseline_observer();w=TerrainWorld(1);results=[]
    for tick in (0,26000):
        started=time.perf_counter();w.step(tick-w.tick);generation=time.perf_counter()-started
        digest=w.digest();population=len(w.living());events=len(w.events)
        for size in ((800,600),(1280,720),(1920,1080),(3840,2160)):
            row=dict(tick=tick,window=list(size),living=population,retained=len(w.agents),events=events,generation_seconds=generation)
            for cls,label in ((reference,'baseline'),(LivingObserver,'folklore')):
                start=time.perf_counter();v=cls(w,paused=True,window_size=size);v.draw()
                row[label+'_startup_seconds']=time.perf_counter()-start
                row[label+'_draw']=measure(v.draw)
                if label=='folklore':
                    row['sprite_layout']=measure(v.sprite_layout)
                    toggle=[1]
                    def zoom():v.camera.zoom(toggle[0]);toggle[0]*=-1;v.draw()
                    row['zoom_and_draw']=measure(zoom)
                    v.follow_id=next(iter(w._living_agents));row['follow_and_draw']=measure(v.draw)
                    counts=(v.presentation.events.records_examined,v.presentation.land.records_examined)
                    row['event_index_sync']=measure(v.sync)
                    assert counts==(v.presentation.events.records_examined,v.presentation.land.records_examined)
                    row['cache']=cache_info()
                pygame.quit()
            assert w.digest()==digest
            row['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            results.append(row);print('Measured',tick,size,flush=True)
            (root/'evidence'/'performance.json').write_text(json.dumps(dict(baseline=BASELINE,driver=os.environ.get('SDL_VIDEODRIVER'),results=results),indent=2)+'\n')
    # Dense fixture is explicitly synthetic, kept separate from natural evidence.
    dense=TerrainWorld(1)
    for a in dense.living():a.x,a.y=20,10
    v=LivingObserver(dense,paused=True,window_size=(1280,720));v.camera.tile=96;v.camera.clamp();v.camera.center_tile(20,10);v.draw()
    dense_result=dict(fixture='60 founders placed on one tile, presentation-only fixture',draw=measure(v.draw),visible=len(v.sprite_layout()[0]))
    pygame.quit()
    # Large-history capture debt measured, not redesigned. Owner world never opened.
    capture_times=measure(lambda:capture_snapshot(w),3)
    save_frames=[];pending_frames=0;worker=None
    v=LivingObserver(w,paused=True,window_size=(1280,720));v.draw()
    with tempfile.TemporaryDirectory(prefix='g8a1-mature-save-') as temporary:
        path=Path(temporary)/'mature.g5.sqlite'
        with game_session(path):
            worker=TerrainCheckpointWorker();started=time.perf_counter();worker.start(w,path)
            capture_ms=(time.perf_counter()-started)*1000;first_tick=w.tick
            try:
                for frame in range(60):
                    pending_frames+=not worker.future.done()
                    start=time.perf_counter();w.step();v.draw();save_frames.append((time.perf_counter()-start)*1000)
                worker.close();loaded=load_game(path)
                assert loaded.tick==first_tick
                loaded.step(w.tick-first_tick);assert loaded.state()==w.state()
            finally:worker.close()
    pygame.quit()
    mature_save=dict(capture_start_ms=capture_ms,frames=len(save_frames),pending_frames=pending_frames,first_tick=first_tick,final_tick=w.tick,
        draw_and_step_median_ms=statistics.median(save_frames),draw_and_step_max_ms=max(save_frames),snapshot_continuation_equal=True)
    result=json.loads((root/'evidence'/'performance.json').read_text());result.update(dense=dense_result,large_history_capture=capture_times,cache=cache_info(),mature_background_save=mature_save)
    (root/'evidence'/'performance.json').write_text(json.dumps(result,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--bench',action='store_true');parser.add_argument('--out',type=Path,default=Path('docs/g8a1'))
    args=parser.parse_args();(args.out/'evidence').mkdir(parents=True,exist_ok=True)
    (benchmarks if args.bench else captures)(args.out)


if __name__=='__main__':main()
