"""Generated-world G8A captures/graphics benchmarks; never opens a player's save."""
import argparse
from functools import partial
import json
import os
from pathlib import Path
import resource
import statistics
import tempfile
import time
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')

import pygame
from gnome_fortress.living_viewer import LivingObserver
from gnome_fortress.terrain_viewer import TerrainObserver
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.game_session import game_session
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.god_viewer import run


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)
def click(pos):return pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=pos)
def slow_save(world,path):time.sleep(.5);return save_game(world,path)


def captures(root):
    folder=root/'captures';folder.mkdir(parents=True,exist_ok=True)
    records=[];world=TerrainWorld(1);v=LivingObserver(world,paused=True,window_size=(1280,720))
    def capture(name,viewer=v):
        viewer.draw();pygame.image.save(viewer.screen,str(folder/(name+'.png')))
        records.append(dict(name=name,tick=viewer.world.tick,living=len(viewer.world.living()),selected=viewer.selected,
            follow=viewer.follow_id,camera=dict(x=viewer.camera.x,y=viewer.camera.y,tile=viewer.camera.tile),
            viewport=list(viewer.viewport),window=list(viewer.screen.get_size()),interventions=len(viewer.world.interventions)))
    capture('00-new-world')
    world.step(120);v.sync()
    movers=[a.id for a in world.living() if a.action=='move' and a.health>=60]
    target=min(movers) if movers else min(world._living_agents)
    v.select_individual(target)
    while v.camera.tile<64:v.camera.zoom(1)
    v.center_selected();capture('01-zoomed-gnome');capture('02-individual-card')
    v.handle([key(pygame.K_c)]);v.paused=False;trace=[]
    for _ in range(30):
        world.step();v.draw();a=world.agents[target]
        trace.append(dict(tick=world.tick,x=a.x,y=a.y,action=a.action,alive=a.alive,
                          camera_x=v.camera.x,camera_y=v.camera.y,follow=v.follow_id))
    capture('03-camera-follow');v.paused=True
    v.follow_id=None;world.step(300-world.tick);v.sync();v.camera.fit();v.feed_mode=2;v.layout(v.screen.get_size())
    capture('04-world-happenings')
    v.feed_mode=1;v.layout(v.screen.get_size());v.camera.zoom(3);v.camera.pan(80,-40)
    pos=v.viewport.center;xy=v.map_target(pos);assert xy is not None
    v.handle([key(pygame.K_e),pygame.event.Event(pygame.MOUSEMOTION,pos=pos)])
    before_rng=world.rng.getstate();preview=v.preview_cells();capture('05-transformed-target-preview')
    v.handle([click(pos)]);p=world.interventions[-1]
    assert (p.x,p.y)==xy and world.rng.getstate()==before_rng
    assert set(world.footprint(p))=={(x,y) for x,y,eligible in preview}
    world.step();v.sync();v.handle([key(pygame.K_t)])
    chosen=(p.changes[0]['x'],p.changes[0]['y']) if p.changes else xy
    v.camera.center_tile(*chosen);v.handle([click(v.camera.tile_rect(*chosen).center)]);capture('06-recorded-land-history')
    world.step(600-world.tick)
    pygame.quit()
    save_trace=[];capture_costs=[];exit_at=[]
    class MeasuredWorker(TerrainCheckpointWorker):
        def start(self,w,path):
            started=time.perf_counter();super().start(w,path);capture_costs.append(dict(tick=w.tick,seconds=time.perf_counter()-started))
    class Inspector(LivingObserver):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);self.frame=0;self.save_requested=True;self.frame_clock=time.perf_counter()
        def handle(self,events):
            self.frame+=1;super().handle(events)
            now=time.perf_counter();save_trace.append(dict(frame=self.frame,tick=self.world.tick,pending=getattr(self,'checkpoint_pending',False),gap_ms=(now-self.frame_clock)*1000));self.frame_clock=now
            if self.frame>=12 and getattr(self,'checkpoint_pending',False):
                capture('07-autosave-running',self)
                exit_at.append(time.perf_counter());super().handle([key(pygame.K_ESCAPE)])
    with tempfile.TemporaryDirectory(prefix='g8a-operational-') as temporary:
        path=Path(temporary)/'capture.g5.sqlite'
        with game_session(path):
            save_game(world,path);start_tick=world.tick
            run(world,path,slow_save,rate=60,max_frames=90,observer_class=Inspector,worker_class=MeasuredWorker)
            drain_wait_seconds=time.perf_counter()-exit_at[-1]
            snapshot_tick=load_game(path).tick;save_metrics=save_game(world,path)
            assert load_game(path).state()==world.state()
        assert save_trace[-1]['pending'] and world.tick>start_tick and snapshot_tick==start_tick
    for size,name in [((800,600),'08-small-window'),((3840,2160),'09-4k-window')]:
        viewer=LivingObserver(world,paused=True,window_size=size);capture(name,viewer);pygame.quit()
    viewer=LivingObserver(world,paused=True,window_size=(1280,720))
    descendant=next((a.id for a in world.agents.values() if a.parents),viewer.selected)
    viewer.select_individual(descendant);viewer.navigate('life');capture('10-personal-history',viewer)
    viewer.navigate('family');capture('11-direct-family',viewer);pygame.quit()
    result=dict(seed=1,fixture='Natural engine updates; only the documented UI Rupture request changes environment',
        human_playtest=False,final_state_digest=world.digest(),family_example_rule='Lowest retained ID with recorded parents',driver=os.environ['SDL_VIDEODRIVER'],moving_selection_rule='Lowest living ID with latest action move and health >=60 at tick120',
        follow_trace=trace,follow_observed_moves=sum((a['x'],a['y'])!=(b['x'],b['y']) for a,b in zip(trace,trace[1:])),
        power_target=xy,preview_exact=True,changed_cells=p.changed_cells,history_inspection_rule='First actual changed cell, else original target',
        save_start_tick=start_tick,drained_snapshot_tick=snapshot_tick,final_saved_tick=world.tick,save_trace=save_trace,snapshot_capture=capture_costs,drain_wait_seconds=drain_wait_seconds,final_save_seconds=save_metrics['seconds'],captures=records)
    (root/'evidence'/'captures.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def measure(callback,count=40):
    times=[]
    for _ in range(count):
        start=time.perf_counter();callback();times.append((time.perf_counter()-start)*1000)
    ordered=sorted(times)
    return dict(samples=count,median_ms=statistics.median(times),p95_ms=ordered[int((count-1)*.95)],
                p99_ms=ordered[int((count-1)*.99)],max_ms=max(times))


def benchmarks(root,ticks):
    world=TerrainWorld(1);results=[]
    for tick in ticks:
        world.step(tick-world.tick);before=world.digest();fixture_living=len(world.living());fixture_retained=len(world.agents)
        old=TerrainObserver(world,paused=True);old.screen=pygame.display.set_mode((1280,720));old.draw()
        old_times=measure(old.draw)
        init=time.perf_counter();new=LivingObserver(world,paused=True,window_size=(1280,720));initial_index_seconds=time.perf_counter()-init
        new.draw();ordinary=measure(new.draw);markers=measure(new.sprite_layout)
        zoom_toggle=[1]
        def zoom():
            new.camera.zoom(zoom_toggle[0],new.viewport.center);zoom_toggle[0]*=-1;new.draw()
        zoom_times=measure(zoom)
        new.follow_id=next(iter(world._living_agents));new.sync();follow_times=measure(new.draw)
        scans=(new.presentation.events.records_examined,new.presentation.land.records_examined)
        update_times=measure(new.sync)
        assert scans==(new.presentation.events.records_examined,new.presentation.land.records_examined)
        assert world.digest()==before
        visible=len(new.sprite_layout()[0]);new_events=len(world.events);world.step()
        start=time.perf_counter();new.sync();append_ms=(time.perf_counter()-start)*1000
        row=dict(fixture_tick=tick,living=fixture_living,retained=fixture_retained,events=new_events,append_tick=world.tick,population_after_append=len(world.living()),
            old_fixed_view=old_times,new_view=ordinary,sprite_layout=markers,zoom_and_draw=zoom_times,
            follow_and_draw=follow_times,no_append_sync=update_times,initial_index_seconds=initial_index_seconds,
            natural_append_update_ms=append_ms,new_events=len(world.events)-new_events,
            incremental_event_records_scanned=new.presentation.events.records_examined-scans[0],
            visible_sprites=visible,state_and_rng_readonly=True,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        results.append(row);(root/'evidence'/'performance.json').write_text(json.dumps(dict(seed=1,driver=os.environ['SDL_VIDEODRIVER'],window=[1280,720],results=results),indent=2)+'\n')
        pygame.quit();print('G8A fixture',tick,'completed',flush=True)
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=Path('docs/g8a'))
    parser.add_argument('--bench',action='store_true');parser.add_argument('--ticks',nargs='+',type=int,default=[0,3000,10000,26000])
    args=parser.parse_args();(args.out/'evidence').mkdir(parents=True,exist_ok=True)
    if args.bench:benchmarks(args.out,args.ticks)
    else:captures(args.out)


if __name__=='__main__':main()
