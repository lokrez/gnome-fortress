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
- Foundation committed as `5dae3be`.
- Gate 2 PASS: Rupture, complete-tick ID ordering, row-major food/terrain ledger
  and terrain-chain validation; 15 focused tests in 3.43s. Bounded seeded demo
  through tick 110 exactly matches midpoint save/reload continuation. No direct
  health changes or RNG draws in isolated activation. No core/legacy files altered.
- G5 committed as `87627ec`.
- Gate 3 PASS: 21 targeted tests in 3.94s. Rewild and single-rock Wellspring
  obey existing regeneration/drinking, ordered transition records, zero direct
  health/displacement/resurrection, pending/completed save replay and no RNG draws
  under isolated activation. Non-rock Wellspring is explicitly zero-change.
  Seed-1 bounded demo preserved all earlier deaths and exact continuation.
- G6 committed as `7927e5c`.
- First G7 integration run: 59 passed, 2 failed. New map-top Land button
  intercepted real map targeting on small terminals, including the save-guard
  test's click. Documented before repair; move Land into the inspection tab row
  and Advisor into the event-header margin in the terrain viewer. Do not relax
  target/save assertions. Legacy hook regression separately passed 34 tests.
- G7 corrected targeted run PASS: 61 tests in 16.70s; all original map-targeting
  and save guards retained. Actual X11 capture: seven screens, 120 running frames,
  final tick 68, Watch preserved, save/reload exact. No artificial biological events.
  Inspected tile-history/Advisor images. Footprint-off legend explicitly says marks
  are hidden. Predeclared 3-seed × 5-condition, 3,000-tick matched protocol before
  any campaign outcomes; benchmark first, bounded full replay/midpoint saves next.
