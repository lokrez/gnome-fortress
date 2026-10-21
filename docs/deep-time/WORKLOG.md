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
  warm median 113.21 ms / worst 147.80 ms; 1.08 s preparation slice outlier. Chronicle
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
- Performance gate committed and pushed as 787edef6137e4577da6283dfb6e997a13c778c51.
- Executed declared 20-seed/6-condition/1,000-generation inheritance campaign
  (9.48 s); repeated it into a separate /tmp output directory. All three CSV
  hashes matched exactly. No production arithmetic changed.
- Ecology pilot: 3.585 s ordinary versus 3.633 s monitored, exact 1k digest. Reported
  projected 4–8 minute cost before launching the declared six 10k worlds.
- Six ecological runs completed in 243.31 s instrumented total, plus the ordinary
  seed-1 replay. That full 10k replay matched canonical state/RNG. No extinctions;
  final populations 359–381,11,537 descendant births, 9,661 deaths.
- Monitored 1,830,130 hunger>=80 gnome-ticks. All had potentially visible edible
  food;20.37% received a decision.3,706 starvation labels, 2,099 with edible local
  stock at biological death. Causal scheduling/survival claims remain untested.
- Research tests passed 3/3 in 23.16 s. Final complete fast suite passed 318 tests in
  276.19 s. No long-run historical archive campaign was executed.
- Separate cold object-graph load probes completed all four scales; actual private
  player load 50.42 s (JSON 11.85, construction including validation 35.62). The
  reader is unchanged. OS page cache was not flushed.
- Inspected actual generated scientific plots for legibility. Real Pygame captures
  and frame traces retained; no human playtest or giant-world UI smoothness
  certification claimed. No optional UI change was necessary.
