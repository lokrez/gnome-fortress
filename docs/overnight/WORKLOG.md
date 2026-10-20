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
- Extra operational verification initially had 3 passes / 1 failure: the new
  autosave-retry test started its world at tick 1, which also initialized the
  loop's last-save tick to 1, so no overdue save was triggered. This is a fixture
  setup error, not evidence of a production retry defect. Repair the fixture by
  requesting a single legitimate step after loop initialization; retain the exact
  two-attempt and final-state assertions. CLI import/corruption, real interrupted
  SQLite process and terrain SIGTERM checks already passed.
- Integrity review reproduced a new G5 API defect before correction: passing a
  legacy GameWorld directly to create_game wrote a G5 envelope with a legacy
  payload, reported success, then failed G5 reload. CLI uses the correct class,
  but the storage API must reject this misuse before writing. Add an explicit
  TerrainWorld type guard and preserve both unused/existing destination bytes.
  Also make new-format integer/record metadata reject bool impostors consistently;
  legacy validators and formats are untouched. Rerun focused and final regressions.
- UI review confirmed another new terrain-view consistency gap before correction:
  T then W opened Life but left tile-targeting enabled; a subsequent map click
  would still inspect land. Clear terrain targeting on Watch/Tab (as already done
  for F1–F3), and on right-click observe. Add a focused state/RNG-preserving test.
  This changes only ephemeral input state, not simulation or terrain rules.
- G7 feature commit: `275c254`. The full initial fast suite passed 220 tests.
- Matched campaign PASS: 15 conditions, seeds 1–3, 3,000 ticks each, fixed
  protocol with 250-tick save/load, independent full replay and 20-tick final
  continuation. All untouched worlds exactly match preserved Phase 3 reference.
  No targets were tuned; CSV death-cause columns were flattened from recorded
  JSON without changing outcomes. Three-seed outcomes are mixed, not survival proof.
- Optional combined seed-1 operational run PASS through 10,000 ticks: 375 living,
  2,063 total, 1,688 recorded deaths, exact replay and save/load continuation.
  Primary 33.84s; replay 32.78s; peak worker RSS 494.3 MiB including verification.
- Profiled before optimizing: map/text rendering dominates frame cost; old-state
  reconstruction and dataclass/JSON encoding dominate checkpoint updates. No
  blocking regression justified optimization. Synthetic 1,000 no-ops explicitly
  labeled; no natural biological claims made from that fixture.
- Final verification PASS: 232 fast tests in 170.17s after integrity/UI fixes;
  22 focused UI/storage/operational tests in 6.73s. Real interrupted SQLite
  process, pending checkpoint input lock, failed-save retry, clean SIGTERM and
  extinct pending-action reload all tested. compileall/diff checks passed.
- Final audit: 538 baseline files preserved (418 research); eleven authoritative/
  legacy modules unchanged, five historical tags exact, four legacy writer/import
  checks with 90-tick continuation, retained fixture continuation, default G4
  state and rendered Life/Advisor pixels exact. Historical CSV normalization only.
- Final safety/documentation commit follows. Push campaign branch, then only safe
  main fast-forward if the remote remains at accepted G4. No G8 or modes started.
