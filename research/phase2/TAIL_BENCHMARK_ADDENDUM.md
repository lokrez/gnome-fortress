# Late-window timing supplement

Added after the 960-slot profile (ticks 3,001–3,200) showed high decision cost hidden
by the full 3,000-tick average. No primary endpoints, rules, seed sets or campaign
horizons change. This is a necessary performance check for a real-time recommendation.

After ALL scientific workers stop, run eight fresh-process bare-original-engine
benchmarks, 200 ticks each: seed 11 at tick 3,000 for all five capacities, and seeds
1,2,3 at tick 100,000 with 60 slots. Load the exact saved checkpoint and external
configuration; exclude loading, hashing and export from loop timing. Record wall,
CPU, RSS (including checkpoint load) and post-window state digest. Do not mix ages
when making capacity comparisons, and do not treat headless timing as viewer frame
latency or a guarantee against future archive-growth slowdowns. No optimization is
performed. The benchmarks fork loaded states and never modify the scientific archives.

Also measure ONE ordinary production SQLite save, separately from the loop, on the
seed-1 loaded 100,000-tick world after its 200-tick timing window. Write a separate
probe file; preserve the scientific input checkpoint. This distinguishes actual
save latency from the more expensive scientific save/load/hash/replay checks and
prevents a headless-loop rate from being mistaken for uninterrupted viewer cadence.
