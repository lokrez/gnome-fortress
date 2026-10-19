# Findings before implementation

- Phase 2 spatial scans iterate all retained identities; dead agents accumulate
  despite a bounded living population. Order of returned peers controls random
  draw consumption and must remain original dictionary insertion order.
- Saving computes the entire recursive world.state() only to discard agents,
  events and cells, then recursively serializes agents again before discarding
  memories and relationships. Every save deletes and rewrites the full history.
- Existing transactional rollback preserves prior checkpoints on SQL exceptions,
  but the loader does not explicitly verify contiguous history sequences or
  checksums. New integrity metadata must not break archived schema-1 loads.
- The observer saves synchronously and redraws at 60 FPS even while paused.
  Its multi-step catch-up can delay controls at high speeds. No rule defect has
  been established; these are performance and operational limitations.

First persistence regression run, before correction: 6 failures, 19 passes.
The new loader omitted the required initial empty parents tuple before ancestry
reconstruction. The streaming writer also inserted relationships to later IDs
before those agent rows existed. Correct by supplying empty parents and deferring
foreign-key checks to transaction commit, where all rows must exist. Existing
triggers and final FK enforcement remain active. No historical files were written.

Crash test finding before correction: SIGKILL after forced page-cache spill left a
hot rollback journal. The legacy read-only URI could not perform SQLite recovery
and raised 'attempt to write a readonly database'. Load will use existing-file
read/write mode only when a rollback journal is present; missing paths still
never create a database. The last committed state must match exactly afterward.

Integrity review before correction: absence of integrity metadata could otherwise
downgrade a new checkpoint to legacy validation. Mark new writes transactionally
with SQLite user_version=2 and require their integrity metadata. Old archives
(user_version=0) remain loadable and the old reader can read new schema-1 tables;
using the old writer to strip new integrity metadata is intentionally rejected.

Preliminary benchmark stopped before acceptance: loader integrity review found
that corrupt header dimensions could be allocated before the stored header hash
was verified. Check the hash and stored cell count before materializing dimensions.
Preserve partial timing outputs, exact prior source and manifest; rerun the final
campaign after correction. No scientific trajectory or historical archive changed.

Rejected mature save benchmark before correction: seed 1 at 100,000 ticks showed
93.17 seconds for a fresh save, versus 7.17 seconds for a repeated save. Component
timing attributed 78.82 seconds to agent SQL and 1.85 seconds to agent preparation.
Deferred relationships to not-yet-inserted agents caused expensive FK sweeps as
agent and child rows were interleaved. Replace this with two passes: write all
changed agent identities, then child records, with normal immediate FK enforcement.
Retain prior source, manifest and partial results; rerun accepted measurements.
Also hash event fields with their parsed detail once, rather than JSON-encoding
detail twice for every historical event. Format markers distinguish checksum
encodings; no event or agent record is omitted.

Pacing review before final UI acceptance: time-budgeted catch-up could accumulate
unbounded wall-clock debt during sustained overload, delaying a requested speed
reduction. Bound pending pacing work to 300 ticks and clear it on speed changes,
just as pause already clears it. This never skips a logical world tick or changes
any decision; it declines to promise catching up indefinitely to elapsed wall time.

Two-pass writer regression, before correction: a broad event-row edit also
changed the SQL insertion generator to return a dict instead of JSON text.
Fourteen focused tests failed with unsupported SQLite bindings; no campaign
was launched or accepted. Restore JSON encoding at the SQL boundary while
keeping parsed details in the checksum stream.

Observer measurement before refinement: the mature real-writer dummy trial
remained interactive (56 ms maximum draw gap), but drew the frozen world 1,309
times and stretched a fresh save to 45.45 seconds versus 15.55 headless.
Redraw only on controls/status changes while saving, and poll at 10 Hz. Measure
actual injected input latency in the revised trial. Headless engine/storage
measurements remain valid and byte-unchanged; record final observer provenance
separately. Preserve prior observer source, harness, results and test evidence.
