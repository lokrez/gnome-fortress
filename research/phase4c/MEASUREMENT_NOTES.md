# Measurement notes

The protocol was fixed before outcome execution; its SHA-256 is
fb5de4cfd7b892cc9a321d25ad3fe23873661eb5e56b13349a3fb093995e1e3f.

The first 38 focused tests passed before the campaign. A 50-tick pilot sample
took 0.206 s (about 14.8 s extrapolated for 3,600 ticks); 100 matrix decisions
took 0.0427 s (about 11.8 s for 27,648). The estimates were reported before
launch. No fixture, seed, matrix value, arithmetic method or horizon was changed.

After the first results, a supplementary evidence exporter was added to recover
full bounded receipt proofs for the 64 original seeds and the already-recorded
forwarded pilot examples. This is an audit of the same trials, not an expanded or
tuned experiment. It replays original worlds and requires the same final digest.
The original campaign outputs remain intact. A separate three-seed, 300-tick
process benchmark measures observer overhead against uninstrumented Phase 4B.
Timing is descriptive, single-run per seed, not a hardware performance claim.

No verified simulation defect was corrected. The negative floor-division fixed
point is an existing arithmetic property under investigation; it remains intact.
Mixed-origin EMA values are not decomposable and are excluded from social-only
readout ablations. No historical archive or endurance run was launched.
