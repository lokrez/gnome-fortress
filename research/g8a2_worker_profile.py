"""One generated mature fixture: actual worker phase and resident memory probes."""
import json,pickle,os,time,tempfile
from pathlib import Path
from dataclasses import replace
from gnome_fortress.chronicle import PreparedPayload
from gnome_fortress.terrain_checkpoint import TerrainCheckpointWorker
from gnome_fortress.game_session import game_session
from gnome_fortress.terrain_storage import save_game
from research.saveguard_profile import profiled_save
_restore=0


class TimedPayload(PreparedPayload):
    def restore(self):
        global _restore
        start=time.perf_counter();world=super().restore();_restore=time.perf_counter()-start;return world


def measured_save(world,path):
    result=profiled_save(world,path);result['restore_seconds']=_restore;return result


def rss():
    return next(int(line.split()[1]) for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmRSS:'))


def main():
    w=pickle.loads(Path('/tmp/gnome-g8a2-generated-fixtures/26000.pickle').read_bytes());before=rss();worker=TerrainCheckpointWorker(measured_save)
    times=[]
    while True:
        times.append(worker.prepare(w)*1000)
        if len(w.events)-worker.chronicle.prepared<128 and not worker.chronicle.dead_queue:break
    prepared=rss();counts=(len(worker.chronicle.blocks),len(worker.chronicle.dead));latencies=[]
    for _ in range(20):
        start=time.perf_counter();payload=worker.chronicle.detach(w);latencies.append((time.perf_counter()-start)*1000)
    after=rss();assert counts==(len(worker.chronicle.blocks),len(worker.chronicle.dead))
    original=worker.chronicle.detach
    def timed(w):
        p=original(w);return TimedPayload(p.hot,p.events,p.dead,p.order,p.full)
    worker.chronicle.detach=timed
    with tempfile.TemporaryDirectory(prefix='g8a2-phases-') as temporary:
        path=Path(temporary)/'mature.g5.sqlite'
        with game_session(path):
            save_game(w,path);start=time.perf_counter();worker.start(w,path);capture=(time.perf_counter()-start)*1000
            metrics=worker.future.result(timeout=120);total=time.perf_counter()-start;worker.poll()
    worker.close()
    Path('docs/g8a2/evidence/worker-phases.json').write_text(json.dumps(dict(tick=w.tick,rss_before_kib=before,rss_prepared_kib=prepared,rss_after_20_captures_kib=after,
        block_counts=counts,preparation_ms=times,main_capture_ms=capture,warm_captures_ms=latencies,total_seconds=total,worker=metrics),indent=2)+'\n')


if __name__=='__main__':main()
