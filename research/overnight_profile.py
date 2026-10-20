"""Bounded profiling before any optimization; synthetic request stress is labeled."""
import argparse
import cProfile
import io
import json
from pathlib import Path
import pstats
import resource
import tempfile
import time

from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game
from gnome_fortress.terrain_presentation import TerrainPresentation
from gnome_fortress.terrain_viewer import TerrainObserver
from .overnight_study import plan,simulate
import pygame


def timed(action):
    start=time.perf_counter();result=action();return time.perf_counter()-start,result


def profile(output):
    output.mkdir(parents=True,exist_ok=True)
    young=TerrainWorld(1);mature,_,_=simulate(1,3000,plan(young,'E'),assert_initial=False)
    stress=TerrainWorld.from_state(mature.state())
    water=next((x,y) for y,row in enumerate(stress.cells) for x,c in enumerate(row) if c.terrain=='water')
    for _ in range(1000):stress.request('rupture',*water,0)
    stress.step();stress.validate()
    results=[]
    for label,w in (('young',young),('mature-combined',mature),('synthetic-1000-noops',stress)):
        validation,_=timed(w.validate);state_time,state=timed(w.state)
        encoding,payload=timed(lambda:json.dumps(state,sort_keys=True,separators=(',',':')))
        index_time,presentation=timed(lambda:TerrainPresentation(w))
        scans=presentation.land.records_examined
        refresh,_=timed(lambda:[presentation.refresh() for _ in range(200)])
        assert presentation.land.records_examined==scans
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.g5.sqlite';save_metrics=save_game(w,path)
            update_metrics=save_game(w,path)
            load_time,loaded=timed(lambda:load_game(path));assert loaded.state()==w.state()
            if label=='synthetic-1000-noops':
                cpu=cProfile.Profile();cpu.enable();save_game(w,path);cpu.disable()
                stream=io.StringIO();pstats.Stats(cpu,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25)
                (output/'save-profile.txt').write_text(stream.getvalue().rstrip()+'\n')
        v=TerrainObserver(w,paused=True);v.tab='terrain'
        try:
            before=w.digest();draw_time,_=timed(lambda:[v.draw() for _ in range(30)])
            assert w.digest()==before
            if label=='synthetic-1000-noops':
                cpu=cProfile.Profile();cpu.enable()
                for _ in range(20):v.draw()
                cpu.disable();stream=io.StringIO();pstats.Stats(cpu,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25)
                (output/'draw-profile.txt').write_text(stream.getvalue().rstrip()+'\n')
        finally:pygame.quit()
        results.append(dict(label=label,tick=w.tick,living=len(w._living_agents),retained_individuals=len(w.agents),
            events=len(w.events),interventions=len(w.interventions),transitions=presentation.land.transitions_examined,
            validation_seconds=validation,state_serialization_seconds=state_time,json_encoding_seconds=encoding,
            payload_bytes=len(payload.encode()),new_checkpoint=save_metrics,existing_checkpoint_update=update_metrics,load_seconds=load_time,
            initial_index_seconds=index_time,steady_refresh_ms=refresh/200*1000,draw_frame_ms=draw_time/30*1000,
            readonly_draw_exact=True,steady_historical_rescans=0))
    report=dict(display='SDL '+pygame.display.get_driver() if pygame.display.get_init() else 'SDL dummy requested externally',
        measurements=results,process_peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        caveats='Single measurements; simultaneous regression/campaign processes may affect timings. Peak RSS includes all three retained fixtures and save/load verification. Synthetic no-op requests are not natural gameplay outcomes.',
        optimization='No optimization attempted without a demonstrated blocking regression.')
    (output/'profile.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    profile(p.parse_args().output)
