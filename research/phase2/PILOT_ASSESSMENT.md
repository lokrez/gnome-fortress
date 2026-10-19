# Pilot assessment and campaign sizing

Measured before launching final campaigns, 2026-10-19:

- Original mature enabled seed 1, ticks 20,000–21,000: 8.601 s unprofiled,
  116.26 ticks/s, 328 MiB process peak RSS (including checkpoint load).
- The same profiled interval took 17.369 s: `_nearby_agents` accounted for 11.486 s
  cumulative (66.1%), versus 0.142 s (0.8%) in scheduler selection. The dominant
  bottleneck is scanning retained identities for local peers, not slot allocation.
- Corrected 1,000-tick fresh-world instrumented pilots: 60 slots 284.1 ticks/s;
  960 slots 149.7 ticks/s, final populations 180 and 198 respectively. At 960,
  process CPU was 99.83% of one logical core and simulation peak RSS 31.3 MiB.
  The short ramp does not represent a mature high-capacity population.

Budget decision (made before final scaling outcomes): keep the pre-specified B
horizon at 3,000 ticks with seeds 11–13, 15 fresh-process timing runs, and full
original-engine replay for seed 11 at EACH capacity. Estimate 5–20 minutes for B,
allowing nonlinear population growth and replay/I/O. Add a small scheduler-only
benchmark; do not expand the behavioral capacity campaign to 20,000 ticks.

A uses the required minimum of 20 matched pairs (1001–1020), not the optional 30
proposed in Phase 1. At roughly 130–180 seconds per 20,000-tick world, estimate
1.4–2 CPU-hours, about 15–30 minutes with six independent workers, depending on
contention and condition-dependent outcomes.

C resumes verified 20,000-tick prefixes for seeds 1–3, saving redundant first-prefix
work. The measured tail gives an optimistic 11.5 minutes per 80,000-tick extension;
retained-identity growth could increase this to roughly 25–40 minutes per world,
plus checkpoint/replay overhead. Three concurrent C runs may take longer under
load. Total phase estimate: roughly 45–90 minutes, not a fixed runtime guarantee.

Run B sequentially before concurrent A/C to avoid hardware benchmark contamination.
Use six scientific workers (independent worlds), keeping the default 60 decisions
per world and leaving headroom on the 8-core/16-thread Ryzen. No GPU work and no
optimization are needed to meet the current minimum campaign; propose indexed peer
queries only as a future equivalence-verified engineering improvement.
