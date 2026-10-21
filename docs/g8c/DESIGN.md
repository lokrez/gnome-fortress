# G8C design before implementation

Keep record blocks, weak invalidation links, immutable historical pickle bytes,
complete-tick hot capture, spawned writer and unchanged G5 persistence.

1. Adopt the existing event list through a read-only-to-observers journal facade
   instead of copying millions of references at first bind. Normal list operations
   retain their behavior; structural edits invalidate event preparation.
2. Adopt the retained-agent mapping through a journal facade. Record insertion,
   replacement and deletion without scanning every old agent at every snapshot.
   New IDs preserve insertion order. Container replacement/deletion/rewind resets
   disposable preparation. Mapping/list aliases bypassing the facade require
   explicit invalidate, just like existing low-level container bypasses.
3. Store immutable metadata in fixed 128-entry tuple chunks. Capture freezes a
   shallow tuple of chunks, not 90k pairs/IDs and 36k block references. Updates copy
   only a changed chunk; previous payloads retain old immutable tuples/bytes.
4. Track explicitly dirty blocks and pending/deceased identities. Capture visits
   living/unprepared records and dirty blocks; clean historical records are not
   reclassified. Canonical agent ordering remains an explicit immutable index.
5. Avoid redundant assignments/wrapping of atomic scalar dataclass fields during
   tracking. Keep recursive watching of all non-atomic owned fields.

No worker receives a live facade or model record. Snapshot bundles contain only
pickle bytes, immutable tuples/chunks and integer IDs. Restore must produce the
same ordered complete state as the full reference. All supported nested edits
invalidate; direct base-list/dict/object bypasses require invalidate(). Internal
cache corruption must still fail closed rather than being hidden by old bytes.

Preparation handles one small block/agent unit at a time with clock checks.
Clock/OS/GC cannot be made a hard real-time guarantee in Python. Report individual
unit outliers and correlated GC explicitly. Cold manual capture remains a coherent
full/tail fallback until a safe scheduling policy is justified; do not pretend it
is cheap. No global GC disable/freeze, schema change, background mutable reads,
biological edit or history truncation.

Verification exposed a required compatibility adapter: the existing canonical
encoder passed `world.events` directly to JSON, relying on its native list type.
The adopted journal is now an explicit encoder case returning its owned list,
without copying it or changing any JSON fields/bytes. This is the only serializer
adjustment; no persistence/schema/validation logic changes. The initial TypeError
and regression logs are retained. It failed before writing a checkpoint.

Observed first candidate: giant warm capture 11–16 ms, but a 1.188-second automatic
GC collection occurred inside event encoding during preparation. This is measured
GC overlap, not a guess about the old run. No GC disable/freeze/threshold change.
Use 1 ms unit headroom in the nominal 4 ms preparation budget (a throughput/latency
tradeoff, not a hard deadline). Rare OS/GC interruptions remain measurable limits.

Owner-loop policy: when an automatic or manual request is due and preparation is
incomplete, keep the existing bounded request flag/interval due and display
“Preparing history for save (last saved T)”. Simulation/navigation continue.
Only a complete prepared capture is submitted; its actual tick is reported.
An early request does not promise a historical tick-T snapshot. Pause freezes the
world if an exact current tick is desired. Direct Chronicle/worker cold capture
retains the full coherent fallback for tools/tests. Clean exit still drains any
writer and synchronously saves the latest world even if preparation is unfinished.
No last-save tick is advanced without a successful committed result.
