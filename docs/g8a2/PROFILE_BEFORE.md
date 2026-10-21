# Before: full-snapshot capture

Executed before runtime changes, seed 1; three probes at each generated checkpoint. Milliseconds below are medians. No player file was used. Phases construct the same shallow graph as the accepted capture; main pickle copies nested memory/learned/relationship/visit values. The phases are instrumentation, not extra production work.

| Tick | Living / retained | Events | Header ms | Episode traversal ms | Event traversal ms | Pickle ms | Total ms | Snapshot MiB | Transfer round trip ms | Worker restore ms |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3,000 | 368 / 607 | 27,162 | 0.16 | 4.79 | 1.47 | 30.53 | 36.93 | 2.76 | 2.84 | 84.44 |
| 10,000 | 373 / 2017 | 107,609 | 0.69 | 17.86 | 6.00 | 148.28 | 172.26 | 9.79 | 10.34 | 286.93 |
| 26,000 | 386 / 5340 | 290,808 | 2.13 | 45.15 | 16.80 | 409.21 | 474.97 | 25.95 | 32.15 | 739.15 |

Terrain/RNG/scheduler/intervention timing is also retained in the raw JSON; terrain was approximately 0.1 ms and RNG approximately 0.01 ms in these probes. The ordinary fixtures have no interventions, so a zero intervention cost is not evidence that large intervention ledgers are free. They remain deliberately uncached and are exercised by five-power replay.

Transfer is a separate warmed pool echo round trip, not an exact disaggregation of kernel copy versus scheduling. Worker restore is separately timed. Disk validation/JSON/SQLite phases are measured in `worker-phases.json` using the existing strict writer algorithm. Existing G8A.1 operational measurements (506 ms capture/start, 467 ms median / 593 ms worst capture) remain historical evidence, untouched.

Cold generation took about 9.8, 23.6 and 56.4 seconds for successive horizons. Verification stops at the explicitly requested 26k representative size. Extending to 100k would require further generation, roughly four times the retained history, and substantially larger full-writer memory/transient JSON. That extension was not needed to prove this bounded latency fix and was not launched. No 50k/100k performance or stability claim is made.

## Isolated non-additive component probes

These three-repeat probes serialize each component independently, so their pickle times cannot be summed to reconstruct full capture (pickle memo sharing differs). They distinguish memory, learned/relationship/visit maps and scheduler from the full-graph traversal. The intervention probe is explicitly a five-request fixture advanced ten ticks, not an ordinary untouched world or a large-ledger benchmark. Full raw build/pickle times and sizes are in `components.json`.

| Tick | Episodes pickle ms | Relationships pickle ms | Learned pickle ms | Visits pickle ms | Living-only pickle ms | Dead-only pickle ms | Scheduler/RNG pickle ms | Five-power record pickle ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3000 | 7.796 | 0.212 | 0.326 | 2.440 | 6.443 | 5.876 | 0.022 | 0.016 |
| 10000 | 30.049 | 0.628 | 1.266 | 8.324 | 6.258 | 42.862 | 0.021 | 0.020 |
| 26000 | 102.017 | 2.600 | 5.203 | 24.298 | 6.076 | 142.983 | 0.024 | 0.017 |
