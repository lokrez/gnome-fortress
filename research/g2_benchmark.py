"""Bounded presentation-only timing; no simulation throughput or enjoyment claim."""
import argparse
import json
import os
from pathlib import Path
import statistics
import time

from research.g2_verify import old_module
from gnome_fortress.game import GameWorld
from gnome_fortress.god_viewer import GodObserver
import pygame


def main(output):
    old,_=old_module('gnome_fortress/god_viewer.py','_g2_old_viewer')
    w=GameWorld(1);w.step(20)
    for kind,x in (('rain',20),('rain',20),('drought',22)):w.request(kind,x,16)
    w.step(100);before=w.digest();rows=[]
    for name,cls in (('G1',old.GodObserver),('G2',GodObserver)):
        v=cls(w,paused=True)
        try:
            v.draw();times=[]
            for _ in range(60):
                start=time.perf_counter();v.draw();times.append(time.perf_counter()-start)
            assert w.digest()==before
            rows.append(dict(version=name,frames=60,window=pygame.display.get_window_size(),
                driver=pygame.display.get_driver(),median_ms=statistics.median(times)*1000,
                mean_ms=statistics.mean(times)*1000,max_ms=max(times)*1000,world_unchanged=True))
        finally:pygame.quit()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(dict(tick=w.tick,living=len(w.living()),timings=rows,
        note='Sequential uncapped rendering, different window sizes; single sample, not a capacity benchmark.'),indent=2)+'\n')
    print(output.read_text())


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output)
