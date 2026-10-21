"""Isolated terrain autosaves: the writer never receives the mutable live World."""
from concurrent.futures import ProcessPoolExecutor, Future
from concurrent.futures.process import BrokenProcessPool
import multiprocessing
import pickle
import os
from pathlib import Path
import random
import signal
import sqlite3

from .terrain_game import TerrainWorld, TerrainIntervention
from .model import Agent, Cell, Episode, Event
from .game_session import checkpoint_write_lock,session_owned
from .terrain_storage import save_game, game_path, recover_game
from .chronicle import Chronicle,PreparedPayload


def _writer_init():
    # Ctrl+C belongs to the interactive parent, which drains the writer and saves
    # the latest live state on exit. Do not interrupt its child transaction too.
    signal.signal(signal.SIGINT,signal.SIG_IGN)


def _save_snapshot(snapshot,path,callback,owner_pid,owned_session=False):
    # A surviving writer must finish before a replacement session may load. A
    # queued orphan must never begin writing a newer owner's timeline.
    try:
        path=game_path(path)
        with checkpoint_write_lock(path):
            if os.getppid()!=owner_pid:
                raise RuntimeError('Checkpoint owner exited before write started')
            if owned_session and Path(str(path)+'-journal').exists():
                recover_game(path,_owner_pid=owner_pid)
            return callback(snapshot.restore() if isinstance(snapshot,PreparedPayload) else pickle.loads(snapshot),path)
    finally:
        # A pool whose parent was SIGKILLed must not become an idle orphan. Kernel
        # exit releases all writer descriptors, including after a callback error.
        if owner_pid>0 and os.getppid()!=owner_pid:os._exit(0)


def _restore_graph(graph):
    world=TerrainWorld.__new__(TerrainWorld)
    world.__dict__.update(graph)
    world.rng=random.Random();world.rng.setstate(graph['rng'])
    world.cells=[[Cell(**c) for c in row] for row in graph['cells']]
    world.agents={i:Agent(**{**a,'memories':[Episode(**m) for m in a['memories']]})
                  for i,a in graph['agents'].items()}
    world.events=[Event(**e) for e in graph['events']]
    world.interventions=[TerrainIntervention(**p) for p in graph['interventions']]
    world._rebuild_index()
    return world


class _Snapshot:
    def __init__(self,graph):self.graph=graph
    def __reduce__(self):return _restore_graph,(self.graph,)


def _record_vars(value):
    data=vars(value)
    return {k:v for k,v in data.items() if not k.startswith('_checkpoint_')} if '_checkpoint_notify' in data else data


def capture_snapshot(world):
    if type(world) is not TerrainWorld:raise ValueError('Terrain snapshot requires TerrainWorld')
    # Flatten dataclass containers without recursive asdict/deepcopy/reducers.
    # These references never cross a tick: pickle detaches the ENTIRE graph before
    # returning to the owner loop. No live references are sent to the child.
    graph=vars(world).copy();graph.pop('_living_agents')
    graph['rng']=world.rng.getstate()
    graph['cells']=[[vars(c) for c in row] for row in world.cells]
    graph['agents']={i:{**_record_vars(a),'memories':[_record_vars(m) for m in a.memories]}
                     for i,a in world.agents.items()}
    graph['events']=[_record_vars(e) for e in world.events]
    graph['interventions']=[vars(p) for p in world.interventions]
    return pickle.dumps(_Snapshot(graph),protocol=5)


class TerrainCheckpointWorker:
    """Capture on the owner thread; spawned child validates/writes detached state.

    Only capture briefly blocks stepping. Once pending, the live world is not
    locked: later decisions/interventions belong to a later checkpoint. The loop
    must use the snapshot's saved tick, not the current live tick, for its interval.
    """
    locks_world=False

    def __init__(self,callback=save_game):
        self.callback=callback
        self.pool=self._new_pool()
        self.future=None
        self.chronicle=Chronicle()

    def prepare(self,world,budget=.004):
        if type(world) is not TerrainWorld:raise ValueError('Terrain preparation requires TerrainWorld')
        return self.chronicle.prepare(world,budget)

    @staticmethod
    def _new_pool():
        return ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'),initializer=_writer_init)

    @property
    def pending(self):return self.future is not None

    def start(self,world,path):
        if self.pending:raise RuntimeError('Checkpoint already pending')
        try:
            path=game_path(path)
            snapshot=self.chronicle.detach(world)
            self.future=self.pool.submit(_save_snapshot,snapshot,path,self.callback,os.getpid(),session_owned(path))
        except Exception as error:
            self.future=Future();self.future.set_exception(error)

    def poll(self):
        if self.future is None or not self.future.done():return None
        future,self.future=self.future,None
        try:return future.result()
        except BrokenProcessPool:
            self.pool.shutdown(wait=True);self.pool=self._new_pool()
            raise
        except Exception as error:
            # Storage failure does not invalidate immutable prepared history.
            if not isinstance(error,(OSError,sqlite3.Error)):self.chronicle.invalidate()
            raise

    def close(self):
        try:
            if self.future is not None:self.future.result()
        finally:
            self.future=None;self.pool.shutdown(wait=True)
