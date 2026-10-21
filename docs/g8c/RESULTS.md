# G8C — Operation Time Flows

G8C reduces repeated history traversal and warm snapshot interruption while preserving complete, exact checkpoints. **It does not eliminate every large-world stall.**

| Measured operation | Accepted reference | G8C |
|---|---:|---:|
| Giant warm capture median, 15 samples | 98.99 ms | 12.26 ms |
| Giant warm capture worst, 15 samples | 157.21 ms | 12.76 ms |
| 26k warm capture median | 13.54 ms | 9.30 ms |
| Giant preparation median / p99 | 4.45 / 4.70 ms | 3.26 / 3.61 ms |
| Giant total cold preparation | 52.93 s | 41.08 s |
| Giant worst preparation call | 90.85 ms | **1166.09 ms** |
| Giant cold full-copy fallback | 13.15 s | 13.12 s |

The preparation worst-case target is **not met**. A generation-1 GC pause of approximately 1.162 seconds was measured inside event encoding. No GC policy was changed. Typical cooperative work is smaller, but Python GC and scheduling still invalidate any hard frame-time guarantee. This finding is retained, rather than hidden by excluding an outlier.

## What changed

The old warm path repeatedly classified 91,003 retained agents and visited clean historical blocks. The new path incrementally tracks births, deaths and replacements, maintains dirty blocks, and freezes copy-on-write metadata chunks referencing immutable prepared bytes. Warm capture copies 376 hot living records at the original giant checkpoint rather than walking all retained history. Initial journals adopt native containers rather than copying millions of references.

Normal owner-loop saves defer while history preparation is incomplete. The existing bounded request remains due and the interface reports preparation. Simulation/navigation continue; the eventual save reports its actual captured tick. An early request is not a promise to save that earlier tick. Pause if the current exact state is desired. Direct tool capture retains a correct, expensive cold fallback; final shutdown still drains and saves the latest state.

## Operational evidence and limits

Real Pygame/Saveguard sessions used SDL dummy and isolated worlds. Giant warm captures were 14.01 and 16.54 ms; 2,667 frame gaps had median 16.55, p95 22.85, p99 27.98 and worst 423.99 ms. The process-pool feeder serialized approximately 547 MB in 331 ms and can hold the GIL; moving serialization to a feeder thread does not guarantee smooth frames. Screenshot/control work is also included in the raw frame trace. Human smoothness approval remains pending.

The first giant child reconstruction took 17.53 seconds, actual fresh-destination SQLite save 26.04 seconds and submit-to-polled-completion 47.57 seconds. This fresh destination is **not comparable to the previous 77.95-second full overwrite**. The later synchronous final overwrite took 85.34 seconds; pending writer drain was not timed separately in that giant run. No background durability speedup is claimed. Owner peak RSS in the giant operational run was approximately 17.47 GiB; profile peak RSS was 11.52 GiB before and after. Complete history and prepared bytes still grow with the world; only transient work/metadata are reused. A single sample is not a stable distribution.

Final regression: **336 passed**. Matched three-seed full-state/RNG/JSON/SHA replay, snapshot mutation checks, legacy/Saveguard regressions and actual giant save/reload continuation passed. Exact scope and initial corrected encoder failures are documented in INTEGRITY.md. No biological, learning, art, camera, terrain, save-format or research balancing changes.

## Recommendation

Owner review can evaluate the much faster warm autosave capture, but this is a partial responsiveness improvement, not a claim that time never stops. Remaining work would need separate authorization: isolate or safely reduce GC traversal during preparation, and reduce GIL-held process handoff without handing mutable state to a worker. Preserve the complete checkpoint/reference tests before attempting either. G8C stops here; no gameplay milestone is started.

See PROFILE_BEFORE.md, PROFILE_AFTER.md, FRAME_TRACE.md, INTEGRITY.md and REPRODUCE.md. Raw samples, failures and intermediate candidate measurements are preserved in evidence.

## Delivery

Implementation commit: `5d6be452d64447da55f8e1939dd49baa5108fb1c`.
Reproduction scripts, full raw measurements and reports are committed separately
on `feature/g8c-time-flows`. Use `git log -2` for the final evidence revision.
Protected-source and player-checkpoint audit passed after the final test run.
Owner review is requested; no human playtest or complete stutter elimination is claimed.
