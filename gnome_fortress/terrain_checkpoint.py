"""Isolated terrain autosaves: the writer never receives the mutable live World."""
from concurrent.futures import ProcessPoolExecutor, Future
from concurrent.futures.process import BrokenProcessPool
import multiprocessing
import pickle
import signal

from .terrain_game import TerrainWorld
from .terrain_storage import save_game


def _writer_init():
    # Ctrl+C belongs to the interactive parent, which drains the writer and saves
    # the latest live state on exit. Do not interrupt its child transaction too.
    signal.signal(signal.SIGINT,signal.SIG_IGN)


def _save_snapshot(snapshot,path,callback):
    # Trusted bytes made by this parent process, never a user checkpoint/file.
    return callback(pickle.loads(snapshot),path)


def capture_snapshot(world):
    if not isinstance(world,TerrainWorld):raise ValueError('Terrain snapshot requires TerrainWorld')
    # One complete-tick, detached object graph; faster than dataclass-to-JSON on
    # the UI thread. Persistence is still the unchanged validated SQLite/JSON.
    return pickle.dumps(world,protocol=5)


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

    @staticmethod
    def _new_pool():
        return ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn'),initializer=_writer_init)

    @property
    def pending(self):return self.future is not None

    def start(self,world,path):
        if self.pending:raise RuntimeError('Checkpoint already pending')
        try:
            snapshot=capture_snapshot(world)
            self.future=self.pool.submit(_save_snapshot,snapshot,path,self.callback)
        except Exception as error:
            self.future=Future();self.future.set_exception(error)

    def poll(self):
        if self.future is None or not self.future.done():return None
        future,self.future=self.future,None
        try:return future.result()
        except BrokenProcessPool:
            self.pool.shutdown(wait=True);self.pool=self._new_pool()
            raise

    def close(self):
        try:
            if self.future is not None:self.future.result()
        finally:
            self.future=None;self.pool.shutdown(wait=True)
