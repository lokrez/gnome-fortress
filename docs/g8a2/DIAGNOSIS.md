# G8A.2 diagnosis

Starting HEAD/main: `3baa31dcb3a7ee5e2d1db14b24259c92235df6dc`, clean. Existing owner PID 402014 and its spawned writer 402234 were inspected read-only and left running. No owner checkpoint was opened. Later descriptor inspection showed a SQLite lock held by the existing writer, but no process-lifetime `.lock` descriptor was visible on that long-running owner. Do not assume an already-running older process acquires new protections merely because files on disk change. All ownership/destructive tests use independent temporary files and processes; the owner must exit normally before relaunching the new build.

## Reference architecture

`capture_snapshot` copied metadata/current terrain/RNG, traversed every retained Agent and Episode and every Event, then pickled the entire graph on the gameplay thread. A spawned child reconstructed the World and used strict G5 storage. This correctly detached tick T, but every autosave paid for all past events and all deceased memories again. Detached writing solved disk blocking, not this initial capture.

The new generated seed-1 fixtures reproduce the reported size: tick 26,000, 386 living / 5,340 retained / 290,808 events. Temporary trusted IPC fixtures live under `/tmp/gnome-g8a2-generated-fixtures`; they are not player saves. [Before data](evidence/before.json) records individual phases, sizes and subprocess reconstruction/transfer probes. The dominant cost is full-graph pickle, followed by Episode/event traversal. Nested learned/relationship/visit mappings are referenced by the shallow header stage and actually copied during pickle, not secretly copied for free.

An initial recursive normalization prototype preserved state but cost 70–97 ms even with prepared history. It was replaced with the existing direct field-flattening technique for mutable records. A second issue was full retained-agent scans on each birth: measured steady-state overhead was about 20%. Monotonic new IDs plus living-to-dead differences removed that recurring scan. Intermediate results are retained; they are not the final accepted numbers.

## Boundaries

No engine/model/terrain rule, camera, art, objective event value, RNG, scheduler, research mechanism or checkpoint format changes. Only checkpoint preparation and one optional per-frame worker hook change existing runtime code. G1–G4's worker has no hook and keeps its previous path. The G5 storage/checksum/SQLite/recovery/session sources remain byte-identical.

A prepared record is not assumed immutable because it is old. See [MUTABILITY_AUDIT.md](MUTABILITY_AUDIT.md): normal Python mutations invalidate serialized history. Workers receive immutable bytes/tuples, never live object references. Cold/incomplete caches retain a safe complete-copy tail and can still be slower.
