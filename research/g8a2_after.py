"""Isolated existing generated fixtures; no player checkpoint access."""
import argparse,json,pickle,resource,statistics,time
from pathlib import Path
from gnome_fortress.chronicle import Chronicle,SegmentedSnapshot
from gnome_fortress.terrain_checkpoint import capture_snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument('--fixtures',type=Path,default=Path('/tmp/gnome-g8a2-generated-fixtures'));p.add_argument('--out',type=Path,default=Path('docs/g8a2/evidence/after.json'));a=p.parse_args();rows=[]
    for tick in (3000,10000,26000):
        w=pickle.loads((a.fixtures/f'{tick}.pickle').read_bytes());c=Chronicle();before=w.digest();cold=[]
        start=time.perf_counter();c.capture(w);cold.append((time.perf_counter()-start)*1000)
        preparations=[];start=time.perf_counter()
        while True:
            preparations.append(c.prepare(w)*1000)
            if len(w.events)-c.prepared<128 and not c.dead_queue:break
        total=time.perf_counter()-start;warm=[]
        for _ in range(7):
            start=time.perf_counter();payload=c.detach(w);warm.append((time.perf_counter()-start)*1000)
        transfer_start=time.perf_counter();blob=pickle.dumps(SegmentedSnapshot(payload),protocol=5);encode_seconds=time.perf_counter()-transfer_start
        assert pickle.loads(blob).digest()==before and w.digest()==before
        old=capture_snapshot(w);assert pickle.loads(old).digest()==before
        row=dict(tick=tick,events=len(w.events),retained=len(w.agents),cold_ms=cold,warm_ms=warm,
            preparation_seconds=total,preparation_calls=len(preparations),preparation_median_ms=statistics.median(preparations),
            preparation_max_ms=max(preparations),snapshot_bytes=len(blob),hot_bytes=len(payload.hot),background_envelope_encode_seconds=encode_seconds,cached_bytes=sum(len(b.payload) for b in c.blocks)+sum(len(b.payload) for b in c.dead.values()),
            rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,exact=True)
        rows.append(row);a.out.write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('measured',tick,row,flush=True)


if __name__=='__main__':main()
