# Mutability audit — before implementation

Baseline 3baa31d; production TerrainWorld only. Research/telephone worlds are not eligible.

| Record | Mutation sites | Reuse policy / invalidation |
|---|---|---|
| Living Agent | engine.py `_biology`, `schedule`, `decide`, `move`, `remember`, `kill`; reproduction also changes the other living parent; social interaction changes both living participants | Never reuse; capture all current fields and nested values at the complete-tick boundary |
| Dead Agent | `kill` removes from `_living_agents`; biology, candidate peers, parents and schedule select living agents only. No production path changes a dead individual afterward. Public Python objects remain writable (e.g. inspection test edits final health). | Cache only after death. Mutation-aware record/container wrappers must invalidate cached bytes on ordinary attribute and nested dictionary/list/Episode edits; replaced identities must be detected. Never assume a dead reference alone proves finality. |
| Event | World.event and GameWorld/TerrainWorld boundaries append Events. No production event edit/removal path. Event.detail and birth parent lists are nevertheless writable. | Segment only detached bytes. Track edits of prepared Event attributes and nested detail structures; journal insertion/replacement/removal/reordering invalidates the prepared prefix. Appends leave prior segments reusable. Rebinding the journal invalidates all segments. |
| Episode | `remember` appends and evicts to 64 while living. No production edits to existing Episode fields. | Living episodes always copied. Prepared terminal episodes require the same mutation invalidation as their owning dead agent. |
| Interventions | requests append; tick boundary activates/expires; regeneration changes totals/ledger; terrain activation appends changes and completion data | Conservative: copy every intervention at capture. No lifecycle-based cache assumption. |
| Terrain | eating consumes food; regeneration; permanent terrain actions | Copy current entire grid at capture, including occupied hazard tiles |
| Scheduler/RNG | every tick/decision; birth/death/sleep; seeded random decisions | Capture exact current state, never prepare across ticks |
| Metadata | tick/next_id/cursor/extinction/origin/initial terrain | Capture through the complete-tick graph; no auxiliary recovery dependency |

The proposed instrumentation is confined to disposable checkpoint code. Wrappers must preserve dataclass field values, dict/list ordering, JSON/asdict semantics and normal mutation behavior; no model, decision rule, event field or save schema changes. Direct low-level bypasses (`object.__setattr__`, `vars(record).update`, calling base dict/list mutation functions on wrapped containers) are outside the supported instrumentation API; explicit cache invalidation is required for such developer edits. They are not production mutation paths. This boundary must be documented and tested rather than claimed as tamper resistance.

Preparation runs on the owner thread between completed ticks, with a budget. No worker reads a live object. Cached history consists of immutable bytes, not trusted references. Cold/incomplete caches use detached current tails or the full safe capture. Cache provenance checks must include world identity, journal identity/revision, tick rewind, record replacement and corrupted payload failure.

## Executed implementation audit

- `engine.py:79` appends Episodes and bounds memories; learning changes only the acting living agent. Hazard memory is recorded before `kill`.
- `engine.py:86` finalizes death and removes the live index. `_biology` (`:94`), scheduling (`:115`) and nearby filtering (`:156`) operate on living agents. Reproduction/social interactions (`:160`) alter only currently living participants. Descendants do not update deceased ancestors' child counts.
- Event producers use new detail dictionaries (kwargs or `dict(...)`); birth parent lists are freshly allocated. Regeneration event amounts are scalar copies, not aliases to intervention totals.
- Agent traits/maps/Episodes are owned per agent in the actual engine; no production shared Episode ownership exists. Tracking therefore has one owning terminal record per nested memory. New engine mutation/alias paths require revisiting this audit.
- Interventions are never frozen: status, parameters, totals, change lists and expiration fields are serialized at each capture, including queued requests at the same tick as an earlier save.
- `EventJournal` retains normal indexing/order. Append/extend preserve cached prefixes; insert/delete/replacement/sort/reverse/multiply invalidate them. Prepared Event fields and nested details have invalidation callbacks. Terminal Agent fields/maps/list operations and Episode attributes do too. Deleting a required field causes controlled serialization/validation failure rather than publishing stale data.
- Dataclass-generated equality originally distinguishes concrete subclasses. The instrumentation explicitly preserves field-value equality against the original classes, including list membership/removal. Tests cover both comparison directions.
- Cache corruption, source replacement, journal rebinding/reordering, cold construction, interrupted preparation and mutation after detach are tested. The worker never dereferences the cache's source weak references; only owner-thread preparation/capture does.

The old `World.state()` exposes the current slots list by reference. One early detachment test accidentally used that aliased list as its supposedly independent oracle. The test now serializes its expected state before deliberately mutating slots in place. The bundle had correctly retained the original slots; no simulation change or relaxed assertion was used to hide that test-fixture error.

Notification ownership is leased per live journal. If a second preparer takes the same World, it invalidates the previous preparer's cache before installing callbacks. Captured in-flight bundles remain immutable. A handoff regression verifies that neither preparer can reuse stale records after subsequent edits. This avoids relying on an unchecked one-preparer assumption.
