# Operation God Complex — work journal

- Start: 2026-10-20 19:29 UTC; authorized window ends 2026-10-21 00:29 UTC.
  Stop new feature work by approximately 00:09 UTC if still active.
- Preflight: clean `main`, HEAD and remote main both
  `0508849cea815f325e87973a06e810ad2e8c41ec`. Created
  `feature/overnight-god-complex`. No unknown changes, tags or archives modified.
- Inspected engine/model, GameWorld/storage, launchers, runtime, G2/G3/G4
  presentation/Advisor, mode contract and gameplay tests. Biological movement
  damages on hazard entry only. Water/rock are impassable for retained identities.
  Complete-tick order is regeneration, biology, scheduling, decisions.
- Plan: separate TerrainWorld subclass, distinct G5 storage/launcher. Reuse inherited
  biology and Rain/Drought regeneration. Version permanent request/transition
  history explicitly; never modify legacy GameWorld/storage or research logic.
- Gate sequence: versioned persistence → Rupture → Rewild/Wellspring → historical
  UI/Advisor → bounded matched comparisons and final preservation/regressions.
  Each feature gate gets tests/evidence and a separate commit before advancing.
- Gate 1 PASS: 28 focused tests in 14.99s; separate headless launch created a
  fresh G5 file at tick 20 and resumed to tick 30. Copy-only legacy import,
  active effect continuation, checksum/version rejection, SQL interruption,
  research protection and exclusive new-file publication verified.
  Foundation commit follows; no legacy source changes.
