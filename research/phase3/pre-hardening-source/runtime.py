"""Operational helpers. Clocks and writer state never enter biological state."""
from concurrent.futures import ThreadPoolExecutor
import json
import sys
import time


class CheckpointWorker:
    """Owner MUST stop stepping while pending; rendering remains read-only."""
    def __init__(self,callback):
        self.callback=callback
        self.pool=ThreadPoolExecutor(max_workers=1,thread_name_prefix='checkpoint')
        self.future=None

    @property
    def pending(self):
        return self.future is not None

    def start(self,world,path):
        if self.pending: raise RuntimeError('Checkpoint already pending')
        self.future=self.pool.submit(self.callback,world,path)

    def poll(self):
        if self.future is None or not self.future.done(): return None
        future,self.future=self.future,None
        return future.result()

    def close(self):
        try:
            if self.future is not None: self.future.result()
        finally:
            self.future=None; self.pool.shutdown(wait=True)


class Statistics:
    def __init__(self,interval=10):
        self.interval=interval
        self.wall=time.monotonic(); self.cpu=time.process_time(); self.tick=None

    def update(self,world,saving=False,paused=False):
        now=time.monotonic()
        if self.tick is None: self.tick=world.tick
        if not self.interval or now-self.wall<self.interval: return
        elapsed=now-self.wall
        print(json.dumps(dict(kind='performance',tick=world.tick,living=len(world.living()),
            ticks_per_second=(world.tick-self.tick)/elapsed,
            cpu_percent_one_core=(time.process_time()-self.cpu)/elapsed*100,
            saving=saving,paused=paused)),file=sys.stderr,flush=True)
        self.wall,self.cpu,self.tick=now,time.process_time(),world.tick


def checkpoint_notice(metrics):
    if isinstance(metrics,dict) and metrics.get('seconds',0)>1:
        print(json.dumps(dict(kind='checkpoint_warning',seconds=metrics['seconds'],
            message='Simulation paused during checkpoint; observer controls remain available')),
            file=sys.stderr,flush=True)
