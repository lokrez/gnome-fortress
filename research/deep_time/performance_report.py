"""Render measured benchmark tables; no extrapolation from small worlds."""
import json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=Path('docs/deep-time/evidence')


def load(name):return json.loads((OUT/(name+'.json')).read_text())


def main():
 lines=['# Deep-time persistence results','',
 'Reference: `72a101727d84a65dd49186503eea765825fa0987`. Same seed-1 worlds; player-scale runs use only the independent private copy, with zero tick advancement. One measured trial per storage cell; these are measurements, not confidence intervals. Some independent regression/probe jobs ran concurrently on this 8-core host; CPU/elapsed phase values are retained in JSON. Do not read sub-millisecond differences as meaningful.','',
 '| World tick | Agents / events | Save before (s) | Save after (s) | Previous validation before / after (s) | Outgoing state+JSON before / after (s) | Peak RSS before / after (GiB) |',
 '|---|---:|---:|---:|---:|---:|---:|']
 before=[];after=[]
 for scale in ('0','10000','26000','player'):
  b=load('before-'+scale);a=load('after-'+scale);before.append(b['save_seconds']);after.append(a['save_seconds'])
  bp=b['save_phases'];ap=a['save_phases']
  outgoing=bp.get('canonical_state_copy',0)+bp['json_encode']
  lines.append(f"| {a['tick']:,} | {a['agents']:,} / {a['events']:,} | {b['save_seconds']:.3f} | {a['save_seconds']:.3f} | {bp['strict_previous_decode']:.3f} / {ap['strict_previous_decode']:.3f} | {outgoing:.3f} / {ap['canonical_projection_and_encoding']:.3f} | {b['peak_rss_kib']/1048576:.3f} / {a['peak_rss_kib']/1048576:.3f} |")
 lines.extend(['','The JSON encoder alone becomes slower with the dataclass default handler; the combined state-materialization + encoding path becomes faster. Peak RSS covers loading plus saving in one process. It is not simultaneous owner+worker memory. Cold loading remains roughly 51–54 seconds at player scale because its strict reader is unchanged.','',
 '## Transaction details','',
 '| World tick | Acquire before / after (ms) | Payload update before / after (s) | Commit before / after (ms) | SQLite bytes |','|---|---:|---:|---:|---:|'])
 for scale in ('0','10000','26000','player'):
  b=load('before-'+scale);a=load('after-'+scale);bp=b['save_phases'];ap=a['save_phases']
  lines.append(f"| {a['tick']:,} | {bp['sqlite_transaction_acquire']*1000:.3f} / {ap['sqlite_transaction_acquire']*1000:.3f} | {bp['sqlite_payload_write']:.3f} / {ap['sqlite_payload_write']:.3f} | {bp['sqlite_commit']*1000:.3f} / {ap['sqlite_commit']*1000:.3f} | {a['file_bytes']:,} |")
 lines.extend(['','SQLite update timings include work done before commit. All writes retain synchronous=FULL. The format and complete canonical logical state are unchanged. Nested parse/validation timings are inclusive and not additive.','',
 '## Actual launcher finalization, private 428,868-tick copy','',
 '| Metric | Accepted launcher | New launcher |','|---|---:|---:|'])
 for key,label in (('load_seconds','Cold load (s)'),('final_save_seconds','Final save (s)'),('post_commit_summary_seconds','Post-commit summary (s)'),('shutdown_excluding_load_seconds','Shutdown save + summary, no pending worker (s)'),('load_save_summary_total_seconds','Whole zero-tick launch, load included (s)')):
  b=load('shutdown-before');a=load('shutdown-after');lines.append(f"| {label} | {b[key]:.3f} | {a[key]:.3f} |")
 lines.extend(['','This executed the real `_launch` headless finalization at zero additional ticks under the private checkpoint’s ownership gate. It is not the earlier timestamp-based 4m26 playtest estimate. A pending worker must still drain before the final owner save; there was no pending worker in this measurement. Never add unrelated benchmark phases and call them a measured shutdown. The separate `checksum-probe.json` measures 0.446 s hashing 891,352,072 bytes in bounded chunks (plus 0.210 s SQLite blob reads); it is a component probe, not an exact writer subphase.','',
 '## Snapshot pauses: unchanged Chronicle, measured separately','',
 '| World tick | Cold full capture (ms) | Preparation total (s) | Worst preparation slice (ms) | Warm capture median / worst (ms) | Feeder pickle (s) |','|---|---:|---:|---:|---:|---:|'])
 for scale in ('26000','player'):
  s=load('snapshots-'+scale);lines.append(f"| {s['tick']:,} | {s['cold_full_capture_ms']:.1f} | {s['preparation_seconds']:.2f} | {s['preparation_max_ms']:.1f} | {statistics.median(s['warm_detach_ms']):.1f} / {max(s['warm_detach_ms']):.1f} | {s['feeder_pickle_seconds']:.3f} |")
 lines.extend(['','**Residual hitch is real.** Chronicle is unchanged: at player scale even warmed capture can exceed 100 ms. A completely unprepared fallback can take seconds; preparation budgets are soft and a garbage-collection/allocation outlier can exceed them. Cold preparation was a tight-loop measurement, not a promise about wall time while playing. Cached bytes grow with retained history; they are not constant memory. No new caching, GC policy or history truncation is introduced to hide these limits.','',
 '## Real Pygame / Saveguard operational runs, generated 26,000-tick fixture','',
 '| Metric | Accepted writer | New writer |','|---|---:|---:|'])
 b=load('operation-before');a=load('operation-after')
 for label,left,right in (('Snapshot capture (ms)',b['captures'][0]['ms'],a['captures'][0]['ms']),('p95 frame gap (ms)',b['gap_p95_ms'],a['gap_p95_ms']),('p99 frame gap (ms)',b['gap_p99_ms'],a['gap_p99_ms']),('Worst frame gap (ms)',b['max_gap_ms'],a['max_gap_ms']),('Background capture-to-completion (s)',b['completions'][0]['pipeline_seconds'],a['completions'][0]['pipeline_seconds']),('Writer save (s)',b['completions'][0]['seconds'],a['completions'][0]['seconds']),('Remaining pipeline/IPC/reconstruction/polling (s)',b['completions'][0]['pipeline_minus_writer_seconds'],a['completions'][0]['pipeline_minus_writer_seconds']),('Final stopped-owner save (s)',b['final_save_seconds'],a['final_save_seconds'])):
  lines.append(f'| {label} | {left:.3f} | {right:.3f} |')
 lines.extend(['','SDL dummy exercised the real renderer, input handling, follow, Decisions, Advisor, background writer, graceful exit and exact reload continuation. Human smoothness feedback is **pending**. No cosmetic/presentation code changed. The final tick differs because the faster writer completes earlier in a running world; compare equal tick 26,600 snapshots, not those final populations. Frame maxima include initialization/preparation and ordinary simulation, not only saving. Do not attribute every frame-gap difference to storage.','',
 '## Remaining engineering work','',
 'Full checkpoint writes remain O(retained history); the reader still parses and rehydrates one complete previous world, and JSON remains a complete document. This deliberately smaller optimization preserves all integrity checks. Further reductions need a separately tested streaming semantic validator or a proven validation-receipt protocol, and a profile-led Chronicle cold/warm preparation design. Replacing full files with auxiliary delta caches is not performed. Large-world final saves still require patience.','',
 'Reproduction commands are in `REPRODUCE.md`; all raw measurements are adjacent.'])
 Path('docs/deep-time/PERFORMANCE_AFTER.md').write_text('\n'.join(lines)+'\n')
 fig,ax=plt.subplots(figsize=(9,5));x=range(4);ax.bar([v-.18 for v in x],before,.36,label='Accepted');ax.bar([v+.18 for v in x],after,.36,label='Optimized');ax.set_xticks(list(x),['0','10,000','26,000','428,868']);ax.set_yscale('log');ax.set(xlabel='World tick',ylabel='Save wall time (seconds, log scale)',title='Complete checkpoint overwrite, identical retained worlds');ax.legend();fig.tight_layout();fig.savefig(OUT/'save-performance.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
