# G8C integrity and preservation

## Executed gates

- Final fast regression suite: **336 passed in 325.85 seconds**. Command: `.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py`. Includes existing Saveguard, lock/crash/recovery, storage, legacy readers, viewer, Chronicle and new mutation tests. No historical endurance/archive campaign was run.
- Focused persistence/Chronicle gate: 69 passed in 103.76 seconds. Earlier encoder-adapter failure logs remain in evidence; both failures were JSON type errors before writing, corrected by an explicit journal projection in the existing encoder.
- Matched seeds 1, 7, 42, each through 3,000 ticks: no preparation, accepted c88b217 Chronicle and G8C agree at 39 declared checkpoints per seed. Complete canonical JSON, RNG, restored snapshots and stored SHA agree. SQL reload followed by 20 more scheduled-input ticks agrees. See `replay.json` and `research/g8c/replay.py`.
- Cold and prepared adversarial snapshots survive later source mutations, events, memories and real terrain actions without changing captured tick-T contents. Supported cache edits are checked against complete-reference capture, including event elements/slices/nested values, deceased memories/relationships, replacement, deletion, rewind and journal replacement. Corrupt prepared bytes still fail closed.
- Actual Pygame sessions ran against private 26k fixtures and the independent giant copy. Giant first committed payload at tick 428868 equals `865f2d2304e3e302650860c25ddbae88d06ecc80323da61f0414bce7682a2611` after the in-memory source had resumed and received Rain. Final tick 430289 reload and 20-tick continuation agree. These are isolated experimental continuations, not changes to the player's world.
- The repeated 26k operational run injected a child-save failure, required explicit retry, drained a pending writer on exit and saved/reloaded the final tick exactly. It measured 6.09 seconds of pending pool drain plus 5.46 seconds of final synchronous save. These are separate costs.

## Mutation contract

Normal record attribute assignments and owned nested watched dictionaries/lists invalidate registered blocks. Journal operations distinguish append from structural edits. Retained-agent insertion, replacement and deletion are tracked; container replacement, rewind or another Chronicle lease rebuilds disposable preparation. Immutable bytes and copy-on-write tuple chunks are the only shared historical snapshot material. Hot terrain, intervention state, agents, scheduler and RNG are pickled before resuming the source.

Direct `object.__setattr__`, base-container bypasses, journal `.data` access, retained pre-adoption native list/dict aliases, and private cache manipulation are **not universally tracked**. A developer using those bypasses must call `Chronicle.invalidate()` before preparation/capture. Explicit cache corruption is rejected by restoration. Production records are owned objects; deliberately sharing a mutable Event/Episode or nested container between otherwise independent record graphs requires cloning or explicit invalidation. No claim of arbitrary Python graph mutation detection is made.

The journal facades are disposable runtime instrumentation. Their pickle representation is an ordinary list/dict. The canonical encoder projects the adopted event list without altering logical fields or bytes. No checkpoint schema, checksum semantics or required external cache files were introduced. No live model references reach the writer.

## Protected boundaries

The final audit in `evidence/preservation-final.json` checks the original file's payload SHA, size and modification time while holding nonblocking shared session/writer gates. It checks all historical tags and byte-compares every unchanged production source against c88b217, including engine/model, terrain rules, intervention implementation, art/camera, Saveguard ownership/recovery and strict transactional storage. Research history and previous evidence are excluded from edits. The original file was never loaded into a progressing World or used as a save destination.

The only production edits are Chronicle and its new index helper, a canonical event-facade adapter, a worker readiness query and the owner-loop deferral of unprepared requests. Old G1–G4 readers and G5 schema/application identity/FULL sync/strict previous-checkpoint validation remain unchanged. This is still prototype recovery, not Ironman.
