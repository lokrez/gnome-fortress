# Measured baseline

Reference c88b217; private closed-world copy, not the owner artifact. First
instrumented run: preparation 55.37 s, maximum 91.28 ms. Bind's initial journal
copy/census alone 91.26 ms. Event block tracking 18.96 s, encoding 7.58 s; deceased
tracking 21.45 s, encoding 6.54 s (inclusive nested timers). There are 36,655 event
blocks and 90,627 deceased blocks. Warm detach calls encode 127,282 times and
classifies 91,003 retained agents even though cached content is unchanged.

The timers themselves distort these tiny cached calls, so the initial warm
numbers in `instrumented-first` are explicitly diagnostic, not the production
latency baseline. The corrected `before` run removes per-block timers before
15 warm samples and cProfile. GC callbacks separately record collection intervals.

A 1.006-second generation-1 collection was observed in the initial cold full
capture, not the 91-ms preparation call. The 21/36-ms event-encode outliers did not
have that same GC attribution. Do not claim the old 1.08-second preparation
outlier has been uniquely explained by GC. Preserve all samples and timestamps.

Confirmed targets for optimization: initial full event-list duplication; repeated
retained-agent classification; repeated enumeration/calls for clean historical
bytes; repetitive scalar-field instrumentation. Preserve complete full-copy
fallback and strict storage. Frame-trace and worker reconstruction measurements
are separate from microbenchmark timings.
