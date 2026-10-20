# Architecture before implementation

The G4 baseline remains the legacy executable reference. New modules implement
an opt-in TerrainWorld and `.g5.sqlite` launcher; old `.g1.sqlite` and research
readers/writers remain intact. No release-mode identity or Ironman claim.

Reuse GameWorld biology, movement, memory, scheduler, extinction and resource
regeneration. All requests share stable contiguous intervention IDs. Rain/Drought
retain their fields, rules and request/activation/expiration events. One-shot
terrain requests use duration zero, a queued→completed lifecycle, ordered row-major
per-cell before/after records, and no RNG. At each complete tick, all activations
run in ID order before inherited regeneration/biology/decisions. Completed terrain
requests are never active regeneration effects.

G5 format carries explicit envelope/record versions, initial terrain at the new
format epoch, provenance of fresh/explicit imported worlds, canonical World state,
interventions and transition records. Validation checks simulation invariants,
event/request consistency, transition geometry/eligibility/order, terrain chains
and final composition. Food snapshots can be checked for bounds and local rule
consistency, not retrospectively inferred through unrecorded consumption.

Explicit import copies a validated legacy state to a new destination, records
legacy format/tick/digest, does not alter source bytes and preserves logical state
and RNG. No automatic conversion. SQLite identity/schema/checksum discriminate
formats. Transactional saves reject corrupt/unsupported files and protect research
paths. New destination creation must refuse overwrite, including import races.
No new recovery journal or rollback enforcement.

Reuse the God viewer through small presentation hooks and a terrain subclass;
legacy controls/behavior remain tested. Terrain indexes are disposable, updated
on appended completed requests, bounded by transitions and map cells, not agents.
Selected-tile history is paged; previews describe current eligibility, not a promise
about future ordered requests. Advisor remains explicit scripted branching.

Matched campaign preregistration will fix map-selection criteria, seeds, timing
and horizon before observing outcomes. Exact schedule replay and midpoint save/load
will be checked; post-divergence RNG use is not an individual causal counterfactual.
