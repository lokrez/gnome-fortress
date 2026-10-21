# Saveguard diagnosis

Starting checkout: main, `52bf735d50c90b90141163934d7a173a1be257ec`, clean.
Accepted G7 `df3a3674fb19104f4be1a0a87c72aabd7474ad16` remains tagged.
Two separately committed stabilization attempts already exist: `cabfe70` moves
terrain checkpoint validation/serialization into a spawned process after a
complete-tick pickle capture; `52bf735` adds a canonical-path flock owner guard.
There is no uncommitted stepped/chunked serializer to discard or replace.

Host inspection found live owner PID 402014 and spawned writer PID 402234;
resource tracker 402041 is not a game. No suspended Gnome Fortress process was
present. The game predates the new launcher guard. Its SQLite handle belonged to
402234 during a write. Save: `run-results/god-terrain/world.g5.sqlite`, 113,307,648
bytes. No WAL/SHM/journal companion existed at that inspection. Read-only
quick_check and checksum verification succeeded at tick 26,317; see
[evidence](evidence/initial-integrity.json). No game was killed, relaunched or
mutated for this directive. No journal/lock files were removed.

## Confirmed mechanisms and gaps

- Original G7 thread checkpoint holds the mutable world stationary for the entire
  operation. This explains the recurring world pause; moving that callback to a
  thread without detachment is insufficient.
- Current terrain worker captures pickle synchronously, then a spawn worker
  serializes/validates/writes independently. Capture scales with retained history;
  its large-world cost needs measurement. There is no mixed-tick chunk assembly.
- Current launcher flock prevents competing updated launchers, including stopped
  owners. Child workers receive no owner FD. However, killing the owner while its
  writer is active releases ownership before that writer necessarily finishes.
  This is a confirmed architectural race by inspection: a new launcher could
  load old state and the orphan could subsequently commit over it. Add an explicit
  writer-drain gate and an orphan-before-write check, then verify in subprocesses.
- Terrain storage validates the live snapshot once, the previous checkpoint once
  before writing and again inside BEGIN IMMEDIATE. Connections are scoped with
  closing(); rollback is explicit. This is expensive but preserves strict checks.
- Current queue is one future plus one boolean manual-save request, not an
  unbounded snapshot queue. Failures pause and suppress automatic retries.
- Old G1 launcher has no session guard. It needs the same ownership discipline.
- Current public writers permit writing an older tick over a newer checkpoint.
  Add transactional non-regression checks without changing the format.

## Plan before implementation

1. Profile identical generated seed-1 worlds at ticks 0, 1,000, 3,000 and 10,000.
   Measure synchronous reference and current detached capture, CPU, frame gaps,
   memory, pipeline phases and exact saved state. Do not use the player's save.
2. Retain coherent complete-tick capture unless measurements justify a safe,
   focused improvement. Preserve JSON/SQLite identities and full histories.
3. Extend owner protection to legacy gameplay and surviving writers; keep bounded
   flow control, explicit failures and final flush. Reject stale-tick writes.
4. Add matched no-save/synchronous/asynchronous replay and subprocess failure
   tests; execute fast regressions, real SDL Pygame smoke and preservation audit.
5. Publish measured limits honestly, commit and push reliability work only.

## Confirmed hot-journal recovery defect (before correction)

A stronger isolated SIGKILL probe set SQLite cache_size=3, updated the checkpoint
with a 2,000,000-byte uncommitted payload, and killed the harness child after page
spill. SQLite left a 115,208-byte hot journal. The original `load_game(mode=ro)`
raised `OperationalError: attempt to write a readonly database`, so ordinary
relaunch could not recover a valid previous checkpoint. The earlier small update
kill test did not force page spill and therefore missed this case.

Correction plan: keep public archive readers read-only; add an explicit active
session recovery reader. Require held session ownership, verify the main-file
SQLite magic/application ID/schema header before opening mode=rw, then let SQLite
recover its own journal and run the original strict full-state reader in a scoped
transaction. Reject foreign/unsupported headers before a writable open; never
create a missing file or manually delete companions. Test both G1 and G5 with
real page-spill/SIGKILL and reject calls outside ownership.

A follow-up failure-path review found that a surviving game retrying after its
writer dies during page spill would still call the read-only prior-checkpoint
reader in the new child. Relaunch recovery alone is insufficient. Extend the
explicit recovery role to the parent's delegated writer, only while it holds the
writer gate and the original parent relationship is live. Recover only when a
rollback journal exists, in the worker, never on the gameplay thread. Add a real
crashed-writer/page-spill/explicit-retry test before final delivery.
