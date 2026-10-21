# G8B performance

Seed-1 generated fixtures, ages 0 / 3,000 / 10,000 / 26,000 ticks. No player save.
Three counterbalanced 180-tick trials per condition, same starting bytes and
inputs, youngest living identity (age then ID) observed. Every resulting digest
matched. The original accepted engine tick loop is the reference; disabled and
observed runs use the new tick bridge. Sixty repeated detailed journal draws at
1280×720; seven warmed Chronicle captures per fixture. Milliseconds below.

| Starting tick | Living | Reference /180 ticks | Disabled /180 | Observed /180 | Observed vs disabled | Warm capture median | Draw median / worst |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 60 | 644.44 | 615.56 | 662.36 | +7.6% | 1.68 | 9.85 / 11.61 |
| 3,000 | 368 | 723.41 | 701.54 | 724.03 | +3.2% | 14.87 | 9.79 / 10.34 |
| 10,000 | 373 | 689.65 | 650.17 | 670.80 | +3.2% | 17.57 | 9.82 / 10.28 |
| 26,000 | 386 | 695.19 | 658.71 | 687.13 | +4.3% | 19.00 | 9.73 / 10.03 |

These short probes have host-load noise; three trials do not establish a precise
confidence interval. Disabled runs happened to be faster than the reference;
that is **not** evidence this feature speeds up biology. The hook performs one
weak-registry lookup per tick. Enabled observation has a measurable cost, roughly
3–8% in these probes. It is not free. At 26k, the observed/disabled difference
corresponds to about 0.98 ms per selected invocation including tick bookkeeping;
it is not an isolated function microbenchmark. Only the selected decision is
traced, and candidate details are not collected for others.

The initial tracer unnecessarily handled helper line events and ignored-frame
locals. Restricting helpers to call/return, and rejecting unknown frames before
reading locals, reduced overhead. `profile-initial.json` records that first
measurement; `profile-sequential-lowest-id.json` records a later sequential probe.
The final benchmark counterbalances order and uses the youngest living identity:
the earlier lowest-ID subject sometimes died early, understating enabled cost.
These are explicitly benchmark refinements, not selected biological outcomes.

## Memory and bounds

- Tick 0: 128 retained tick records, 857,757 bytes of recursively measured value storage.
- Tick 3,000: 128 retained tick records, 372,790 bytes of recursively measured value storage.
- Tick 10,000: 128 retained tick records, 339,565 bytes of recursively measured value storage.
- Tick 26,000: 128 retained tick records, 321,405 bytes of recursively measured value storage.

Every memory-probe world was released after deletion/GC while its trace remained
inspectable. The record-value walker rejects model/frame objects. Dense synthetic
unit tests verify the 64-peer and 64-random-attempt caps, with full scalar counts.
No all-agent observation archive exists. Tick, ring and primitive value limits
bound the observer, independently of retained objective history.

The full profiling process reached roughly 1.14 GiB peak RSS while also creating
multiple worlds and canonical state/digest copies; this is not observation-only
memory. The separate memory probe peaked around 404 MiB at the mature fixture.
No new worker-specific RSS probe was performed; persistence worker code is
unchanged. These measurements do not promise constant memory for the simulation's
complete growing history.

## Actual X11 operation

Generated 26k world; 1280×720, observation and follow enabled for #05340.
Autosave captured tick 26600 in **18.69 ms**;
the worker completed in 9.06 s. It wrote a complete
106,868,736-byte checkpoint. Simulation, feed, Advisor
navigation and a Rain request remained operational. Final exit saved tick
26909; reload plus 30 ticks matched exactly at 26939.

Across the operation, worst frame gap was **153.79 ms** (cold-start
frame 2 at tick 26000, no save pending); worst pending-save gap was
**89.88 ms**. Frame-gap p99 was approximately 32.12 ms.
Capture and PNG automation are included; this is not a human smoothness assessment.
The warm save no longer has the former half-second capture interruption, but
cold history preparation, draw work, GC and occasional frame stalls remain.
G8B does not claim to solve those existing startup/cold-save limitations.

Full frame samples, capture timings and commit metrics are in `evidence/operation.json`.
The operational script casts at its first pending-save frame; wall-clock automation
can produce different intervention ticks between operational runs. Scientific
replay tests instead fix intervention inputs by simulation tick.
