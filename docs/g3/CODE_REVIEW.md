# G3 targeted code review — before implementation

Reviewed accepted G2 `307e511335c6102e72e45d836dd8f07550271027` on clean main.
All references below identify **that commit's** lines, so remain stable after G3.
Scope: engine/model, game/storage, presentation/viewer, runtime/launcher, gameplay
and presentation tests, G1/G2 reports and compatibility results. No critical or
major defect was confirmed. Source inspection is distinguished from executed
verification in the final G3 report; this review itself is not an endurance test.

## Findings

| Severity | Reference at G2 | Finding / disposition |
|---|---|---|
| Minor | `gnome_fortress/god_viewer.py:276-287` | After a periodic save fails, `last_save` stays old, so the same overdue condition immediately schedules another save, even while paused. Confirmed control-flow issue; reproduce in a bounded test and suppress automatic retries until an explicit save succeeds. Keep inspection responsive and retain final explicit exit-save behavior. Directly related to watching a long-running world. |
| Minor | `gnome_fortress/god_viewer.py:175-183` | A deceased individual's stored coordinates are labeled merely “location.” They are final stored coordinates, not a moving live position. Clarify in G3 inspection; no model correction. |
| Architectural debt | `gnome_fortress/engine.py:49-59`, `gnome_fortress/model.py:42-45`, `gnome_fortress/game_presentation.py:7-29` | Objective events, retained identities and derived global index grow with a run. Incremental indexing already avoids per-frame full event scans. G3 must not add a persistent biography archive or all-agent timeline cache. One selected-agent index is sufficient; an initial selection scan is allowed and documented. No claim of fixed total memory indefinitely. |
| Architectural debt | `gnome_fortress/viewer.py:83-109`, `gnome_fortress/god_viewer.py:140-158`, `gnome_fortress/game_presentation.py:83-107` | Rendering sorts retained living/dead identities and draws the whole map; overlap derivation scales with active areas. Large populations/history can increase frame cost. No measured critical responsiveness failure is established. Keep G3 work bounded per visible page and measure small synthetic cases; defer unrelated engine/render refactors. |
| Architectural debt | `gnome_fortress/game_storage.py:48-69`, `gnome_fortress/god_demo.py:29-53` | Full JSON snapshots, validation and old-save reads grow with history. Transactions/checksums and fail-closed loading exist, but crash-recovery journals/fallback and Ironman enforcement do not. G3 changes no save format or recovery promise. |

## Required semantics confirmed, not defects

1. **Simulation/view separation.** `god_viewer.py:71-117` creates explicit requests
   or calls existing complete-tick stepping. `game_presentation.py:49-57` copies
   display fields; `game.py:39-109` owns intervention validation, timing and resource
   effects. Derived indexes live in the observer, not World state. Preserve this.
2. **Determinism/RNG.** `engine.py:206-247` owns movement RNG and ordered candidates;
   `game.py:59-77` applies scheduled effects without new draws. UI formatting,
   browsing, selection and drawing must never access RNG draws. Existing
   `tests/test_game_presentation.py` and `tests/test_god_viewer.py` cover nonmutation
   and render cadence; extend them for Life/Watch/family.
3. **Event attribution.** `engine.py:52-59` records births including parent IDs;
   `engine.py:187-196` records reproduction with actor/partner/child; `engine.py:198-206`
   records directed social encounters; `engine.py:86-92` records death. Include
   actor, target and explicitly recorded child/parent roles, not mere spatial or
   temporal proximity. Social values are directional numbers, not friendships.
4. **Age and history.** `engine.py:45-47` creates founders at age 120..300 but born
   tick 0. `model.py:27-38` stores birth, age and death separately. Display those
   facts independently. `engine.py:79-84` evicts episodes beyond 64; this does not
   erase objective events. Paths and lifetime eating history are not recorded.
5. **Living/sleeping/deceased selection.** `game_presentation.py:49-57` derives life
   status; `viewer.py:54-63` cycles IDs, including dead records. IDs are retained
   after death. Death does not already force selection to another agent. Add Watch
   explicitly, retain a dead watched ID and guard missing/incomplete inspection
   records. The selection marker is already painted above overlapping icons.
6. **Save/load.** `game_storage.py:24-45` verifies format/checksum and reads a pinned
   snapshot. The accepted G2 compatibility report verifies G1 writer/reader and
   exact recorded outcomes. G3 must continue using `.g1.sqlite` format v1. UI
   selection, scroll and Watch reset on a new observer; none is persistent world
   state. Saving within an open observer must retain the selected/watched ID.
7. **Long-running responsiveness.** `god_viewer.py:266-297` uses a checkpoint worker;
   ticks and casts freeze during writes, observation remains serviced. Inherited
   `viewer.py:67-81` budgets catch-up between complete ticks. Initial load/indexing
   and one heavy tick can still block; no finite smoke test proves indefinite
   responsiveness. Address the retry loop above without changing pacing rules.
8. **Extinction.** `game.py:59-77` stops time when empty and `god_viewer.py:112-117`
   pauses automatic progression. `god_demo.py:50-53` still saves on exit. This is
   the prototype, not the future read-only Ironman chronicle. Life can inspect
   final records without resuming or resurrecting the run.

## G3 implementation boundary

New read-only Life helper and tab; one selected individual's chronological event
positions, direct family IDs and visible-page formatting. Incrementally process
appended events/identities. Release old personal indexes on selection changes;
no recursive ancestry tree or significance ranking. Watch is ephemeral UI state;
manual selection stops watching, death does not. Keep God powers and G2 global
feed. Fix only the documented viewer retry/location issues. No changes planned to
engine, model, game rules, storage, release-mode contract or experimental channels.
