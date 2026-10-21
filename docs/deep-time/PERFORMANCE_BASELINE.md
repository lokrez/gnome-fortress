# Deep-time baseline

Reference: `72a101727d84a65dd49186503eea765825fa0987`. Linux, Python 3.14,
local SQLite; one independent copy of the player's closed checkpoint. No ticks
advanced. Source preservation is recorded in `evidence/artifact-preservation.json`.

The private 428,868-tick copy contains 91,003 agents and 4,691,860 events.
`research.deep_time.profile_storage` measured:

| Phase | Wall seconds |
|---|---:|
| Cold load, checksum, decode, reconstruction and validation | 51.225 |
| Complete overwrite save | 142.234 |
| Previous checkpoint reconstruction (two calls) | 103.699 |
| Outgoing recursive canonical-state materialization | 18.913 |
| Outgoing JSON encoding | 12.532 |
| SQLite transaction acquisition | 0.000016 |
| Payload update | 1.052 |
| Commit | 0.000040 |

Peak process RSS was 16,256,892 KiB (15.50 GiB), 8,262,524 minor page faults,
zero major faults. Payload is 891,352,072 bytes; resulting private SQLite file
1,779,752,960 bytes. RSS covers load plus save, not the two-process running game.
Phase timings are **inclusive**: JSON parsing and validation inside `_read` are
already included in its total and must not be added again. Commit is measured
separately from SQLite's update work; a small commit value does not imply that
writing or synchronization was free.

The prior 4m26 shutdown estimate includes a different workload (possible worker
drain, final save and final digest); it is not this instrumented save measurement.
Fresh and generated-world results are supplied alongside the final comparison.
