# Deep Time execution journal

- Started at 72a1017 on clean main; created feature/deep-time. No live/suspended
  game found. Read the October 21 report; copied the closed player database once
  under shared ownership/writer gates into a distinct /tmp inode.
- Generated seed-1 isolated fixtures by stepping TerrainWorld to 1k, 3k, 10k and
  26k and storing local protocol-5 pickles. Generation to 26k took 99.13 s.
- Baseline actual private-copy overwrite: 142.23 s, two previous-world decodes
  103.70 s; SQLite update only 1.05 s. No ticks advanced in the real-history copy.
- Implemented one in-transaction full prior validation plus read-only metadata /
  inode preflight, mode=rw, identity rechecks. Retained strict reader and checksums.
- Added canonical dataclass projection; exact byte tests include all five powers,
  Chronicle subclasses, nested mutations, Unicode and integer relationship keys.
- Private giant-copy save: 77.95 s. Peak RSS 15.50 ->14.71 GiB. Actual launcher
  final save/summary: 180.38 ->78.54 s, no pending worker; same canonical digest.
- Protected original and rewritten private copy verified against original SHA.
- Snapshot probing found remaining scaling debt: 13.57 s completely cold capture,
  warm median113.21 ms / worst147.80 ms; 1.08 s preparation slice outlier. Chronicle
  unchanged. Do not claim universal stutter elimination.
- New test development failures: a 1k fixture had no deceased agents (extended to
  3k natural history); a direct launcher fixture omitted its db argument and
  session ownership (corrected to use the real gate). A reference-loader benchmark
  initially omitted __file__, then its Namespace db; fixed before measurements.
  These were fixture errors, not production data defects. Failed/interrupted logs
  are preserved. The corrected complete fast suite passed 315 tests in 249.80 s; the final
  focused storage/Chronicle/Saveguard suite passed 47 in 73.81 s.
- Real Pygame SDL-dummy operations used disposable 26k worlds, actual renderer,
  background checkpoints, Advisor, follow/Acts and exact continuation. Human
  playtesting remains pending. No art, camera, UI or biology source changes.
- Inheritance/starvation protocols and source audits written before scientific
  trials. No production rule variants introduced. Performance is committed first.
