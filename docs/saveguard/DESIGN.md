# Saveguard design

The simulator remains authoritative and single-threaded. Saving is operational;
no biological state, event meaning, RNG consumption, tick order or save schema
changes are authorized. G7 remains the preserved behavioral baseline.

## Ownership and writer lifetime

A canonical-path `.lock` uses nonblocking Linux flock, acquired before load,
create or import and held through final save and writer shutdown. Persistent
sidecars are not removed; PID text is diagnostic only. O_CLOEXEC and spawn prevent
accidental descriptor inheritance. Apply this to both gameplay launchers.

Add a separate `.writer.lock` transaction gate. A background child takes it before
opening SQLite and confirms its original parent still owns the process relationship.
A new session, after taking the owner lock, must pass the same writer gate before
loading. Thus a killed owner cannot leave a writer concurrently committing against
a replacement session: an already-started orphan write drains first, or a delayed
orphan refuses before opening SQLite. No busy wait or arbitrary lock stealing.
The worker deliberately owns only its writer-gate descriptor, never the session
lock. If the parent is gone after a completed write, the child exits rather than
remaining as an idle orphan. Test both sides of the parent-death race.

## Coherent capture and bounded flow

Capture executes entirely on the owner thread between complete ticks. No worker
reads the live World. Trusted snapshot bytes cross a spawn-process boundary;
user files remain checksummed, strictly validated JSON in SQLite, never pickle.
Performance changes to capture must preserve exact graph/state/RNG and be measured.
There is one active future and one boolean explicit retry/request, not an array
of snapshots. No pending replacement snapshot is allocated. Periodic requests
coalesce until the current writer completes. One manual request during a write
requests one fresh snapshot afterward. Completion reports the captured tick.

Failures preserve the previous commit, visibly pause, suppress automatic retries,
and allow explicit S. A success clears the error but does not silently resume.
Exit drains the active future, then saves the latest owner-thread world while
still holding ownership. A shutdown save may block. If draining fails, the
launcher's finally still attempts the final full save and reports failure.

## SQLite

Retain FULL synchronization and rollback-journal transactions; WAL is unnecessary
for one world owner/one writer. Read-only validation connections close before
BEGIN IMMEDIATE. The transaction validates the pinned previous checkpoint again,
rejects decreasing ticks, writes the full new payload/checksum, and commits.
Rollback/connection close occurs on every error. Same-tick updates remain allowed
because requests can be accepted while paused. No in-place schema migration.
This is prototype persistence, not Ironman or a command-recovery journal.

## Validation

Use generated seed-1 worlds, temporary databases and harness-owned subprocesses.
A tick-based five-power input schedule compares no-save, synchronous and detached
runs. State and RNG are compared at snapshot ticks, then after identical future
inputs. Failure tests cover suspension, kill, orphan writes, duplicate input,
corruption, interrupted transactions, extinction, legacy imports and shutdown.
Real Pygame/SDL-dummy draws measure frame gaps; this is automated operational
coverage, not a human judgment of smoothness or enjoyment. Keep full distributions
and sample counts; do not hide capture outliers or claim a zero-cost capture.

## Implemented capture representation

Profiling confirmed reducer overhead in serializing the entire retained object
population. The optimized capture builds ordinary container views of the current
world, cells, agents, episodes, events and interventions. Within the same uninterrupted
owner-thread call it pickles the entire graph into detached bytes. No shallow
references survive into the worker. The child reconstructs the same dataclasses,
restores the exact RNG and rebuilds only the derived living-agent index. Strict
storage validation still runs. There is no freeze-by-chunks algorithm and no
assumption that old events/dead agents are immutable. All retained history is
captured every time. Snapshot restoration accepts trusted IPC only; public G1/G5
readers still parse and validate their original JSON/SQLite formats.

This change targets terrain gameplay. Legacy G1 gets ownership and decreasing-tick
protection but retains its original synchronized checkpoint worker as a compatibility
path; it does not receive a claim of smooth asynchronous terrain autosaves.
Direct low-level storage callers remain responsible for session ownership; these
advisory locks are not a security boundary against SQLite tools or modified code.
Canonicalization merges symlink aliases, not independently created hard links.
Already running pre-guard versions must exit before relaunching updated code.

## Crash rollback without writable archive reads

The page-spill SIGKILL probe exposed a separate loading defect. Active launchers
now call an explicit `recover_game` inside `game_session`, rather than the public
read-only archive loader. Recovery checks ownership in a PID-scoped process-local
registry (the flock remains the actual authority), then inspects the 100-byte
SQLite header for magic, application ID and schema version. Unsupported/research
headers are refused before a writable SQLite open. `mode=rw` never creates a file.
SQLite performs its own hot-journal rollback; the original strict checksum/state
reader then validates the committed snapshot. Connections close before execution.
No application code deletes journals, WAL/SHM or lock files. No schema changes.
Public `load_game` remains read-only and may correctly refuse a hot journal until
an authorized active session performs recovery. A damaged journal that SQLite
cannot recover remains an error; no alternate state is invented or silently reset.

A surviving owner's explicit retry may also face a hot journal after its child
crashes. The replacement worker receives an explicit parent-session delegation,
holds its own writer gate, checks the live original PPID, and invokes recovery
only when a rollback journal exists. Recovery validates the same header and full
checkpoint in the child, not the gameplay thread. A process-local writer registry
tracks that descriptor's scope. No unrelated subprocess receives ownership and
no routine main-thread validation/read was added. Tests kill a writer after real
page spill, then retry successfully without terminating the owner.
