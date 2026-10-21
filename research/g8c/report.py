"""Summarize all raw samples without deleting outliers or inventing GC causes."""
import json,statistics,math
from pathlib import Path
ROOT=Path('docs/g8c');OUT=ROOT/'evidence'


def quantile(values,q):
 v=sorted(values);r=(len(v)-1)*q;a=int(r);b=math.ceil(r)
 return v[a]*(b-r)+v[b]*(r-a) if a!=b else v[a]


def distribution(values):return dict(n=len(values),median=statistics.median(values),p95=quantile(values,.95),p99=quantile(values,.99),worst=max(values))


def cell(values):return ' / '.join(f'{v:.2f}' for k,v in distribution(values).items() if k!='n')


def main():
 summary={};lines=['# G8C measured profile after','',
 'Reference c88b217. Same private original-state copy and seed-1 generated fixtures. No original-world stepping/writes. Unit timers remain during preparation; they are removed before 15 warm samples. Percentiles use linear interpolation and are descriptive, especially with only 15 warm samples. Raw outliers remain included. Independent regression/operation jobs sometimes ran concurrently on this 8-core host.','',
 '| Scale | Preparation ms: median / p95 / p99 / worst, before | After | Warm capture ms: median / p95 / p99 / worst, before | After |','|---|---:|---:|---:|---:|']
 for scale in ('0','26000','player'):
  b=json.loads((OUT/'before'/f'{scale}.json').read_text());a=json.loads((OUT/'after'/f'{scale}.json').read_text())
  bp=[s['ms'] for s in b['preparation']];ap=[s['ms'] for s in a['preparation']]
  lines.append(f"| {a['tick']:,} | {cell(bp)} | {cell(ap)} | {cell(b['warm_ms'])} | {cell(a['warm_ms'])} |")
  summary[scale]=dict(before=dict(preparation=distribution(bp),warm=distribution(b['warm_ms'])),after=dict(preparation=distribution(ap),warm=distribution(a['warm_ms'])))
 lines+=['','| Scale | Cold full-copy ms before / after | Total preparation seconds before / after | Feeder pickle ms before / after | Peak RSS GiB before / after |','|---|---:|---:|---:|---:|']
 for scale in ('0','26000','player'):
  b=json.loads((OUT/'before'/f'{scale}.json').read_text());a=json.loads((OUT/'after'/f'{scale}.json').read_text())
  lines.append(f"| {a['tick']:,} | {b['cold_full_ms']:.1f} / {a['cold_full_ms']:.1f} | {b['preparation_seconds']:.2f} / {a['preparation_seconds']:.2f} | {b['feeder_pickle_ms']:.1f} / {a['feeder_pickle_ms']:.1f} | {b['peak_rss_kib']/1048576:.2f} / {a['peak_rss_kib']/1048576:.2f} |")
 lines+=['','Warm giant capture meets the 50/100 ms targets in these 15 samples. Preparation median/p95/p99 meet 4 ms, but the worst does **not** meet 16 ms: a 1.162-second collection was measured during an event encode. Small additional outliers are not assigned a cause without evidence. The first candidate also showed this; it is not hidden or called resolved. Cold full-copy remains seconds and is not a normal owner-loop save path while history is unprepared.','',
 'The earlier 91-ms first bind copied the event list. The new bind adopts it; retained ID metadata is initialized once. No warm historical-agent census or clean-block encode loop remains. The cProfile calls show only 376 hot agents at the giant snapshot versus 91,003 retained records before. Hot pickle/flattening is now the dominant capture work.','',
 'Copy-on-write metadata adds bounded reference chunks proportional to history. One in-flight save retains old immutable versions only while needed. Cached payload bytes and full canonical history still grow; this is not constant-memory storage. No GC policy, checksum, strict validation, format, old evidence or biology changes.','',
 'Run commands and contracts are in DESIGN.md and INTEGRITY.md. The first instrumented run timed every cached encode and overstated warm latency; it is preserved under instrumented-first, excluded only from the uninstrumented warm comparison with that explicit reason. indexed-first is the pre-headroom candidate, also preserved.']
 (ROOT/'PROFILE_AFTER.md').write_text('\n'.join(lines)+'\n')
 frames=['# Actual Pygame frame trace','',
 'Real LivingObserver/owner loop and spawned Saveguard writer. SDL dummy, 1280×720. No human smoothness approval is claimed. Private generated/copy worlds only. All frame gaps are retained, including startup, automated control/screenshot work, GC and feeder interference. Percentiles are observed distributions, not guarantees.','',
 '| Session | Frames | Frame gap ms: median / p95 / p99 / worst | Capture ms: median / p95 / p99 / worst |','|---|---:|---:|---:|']
 ops={}
 for name,path in [('26k warm',OUT/'operation'/'26000.json'),('26k cold preparing',OUT/'operation-cold'/'26000.json'),('giant warm',OUT/'operation'/'player.json'),('26k repeated, drain timed',OUT/'operation-final'/'26000.json')]:
  if not path.exists():continue
  d=json.loads(path.read_text());gaps=[f['gap_ms'] for f in d['frames']];captures=[c['ms'] for c in d['captures']]
  frames.append(f'| {name} | {len(gaps)} | {cell(gaps)} | {cell(captures)} |')
  ops[name]=dict(gaps=distribution(gaps),captures=distribution(captures),final_save_seconds=d['shutdown_seconds'],drains=d.get('drains','not separately timed in this earlier run'),
    feeder=[dict(ms=(f['end']-f['start'])*1000,bytes=f['bytes']) for f in d['feeder'] if f['bytes']>10000],
    first_reconstruction=d['completions'][0]['reconstruction_seconds'],first_pipeline=d['completions'][0]['pipeline_seconds'])
 frames+=['','Per-frame simulation/render times, preparation progress, GC thread/context, owner capture times, pool feeder serialization and save/reconstruction/completion metrics are in the raw JSON. Input scripts exercised selection, follow, Advisor, Decisions, Land and a genuine Rain request while the writer was pending. The 26k sessions also injected a controlled child-save failure and explicit retry.','',
 'The cold 26k session starts unprepared: the manual request remains pending while the actual world advances; the loop does not call the full cold fallback. Its first saved tick is later than the request tick and is reported truthfully. Warm sessions explicitly prepare before opening the viewport; their warmup costs are recorded, not concealed as gameplay.','',
 'At giant scale the first manual snapshot is captured while paused at 428,868, then the world resumes and receives Rain before the worker finishes. The first full saved JSON SHA must equal the private original checksum. Exit drains any newly pending writer and synchronously saves the latest tick; reload and 20 further ticks are checked against uninterrupted state.','',
 'A pool feeder runs in another thread but may hold the GIL while pickling hundreds of MB. Its measured serialization is not owner detach time. GC and feeder stalls remain potential visible hitches, even with fast warm capture. Do not equate SDL dummy frame timings with human-perceived smoothness. Giant final owner save is timed separately; earlier runs did not separately time pool drain. The later repeated 26k trace records it explicitly.']
 (ROOT/'FRAME_TRACE.md').write_text('\n'.join(frames)+'\n')
 (OUT/'summary.json').write_text(json.dumps(dict(profiles=summary,operations=ops),indent=2)+'\n')

if __name__=='__main__':main()
