# Phase 3 evidence and reproduction

The oracle in `reference/` is a byte-exact copy of the six production modules at
`5efc9b1bfdd8d49a13aefd4e9256e6c1e87c024f`. SOURCE.json records SHA-256 values.
Do not substitute the current engine for this oracle. All historical test files,
research scripts, datasets, checkpoint bytes and tags remain preserved.

## Commands

From a fresh checkout with the historical checkpoints present:

```bash
.venv/bin/python -m research.phase3_profile
.venv/bin/python -m research.phase3_benchmark
.venv/bin/python -m research.phase3_observer
.venv/bin/python -m research.phase3_after
.venv/bin/python -m research.phase3_equivalence
.venv/bin/python -m pytest tests research -q -s
.venv/bin/python -m research.phase3_archives
```

The benchmark refuses existing output folders. Copy a JSON in `specs/`, choose a
fresh `name`, and run `python -m research.phase3_benchmark --case copied.json` to
repeat an individual case. The young case uses seed 11 and 3,000 ticks. Mature
cases resume the original seed-1 tick-20,000 checkpoint and all three Phase 2
seed-1/2/3 tick-100,000 checkpoints, with 200 measured ticks. No historical input
file is written. Regenerate missing historical inputs in a separate checkout of
phase2-verified using its original instructions; the historical runners retain
baseline source guards and must not be silently redirected to the current engine. Reference and optimized jobs execute sequentially in fresh
processes; order alternates by case. CPU frequency, thermals and other desktop
activity are not forcibly controlled. These are local measurements, not universal
throughput guarantees.

Raw result JSON and newly written SQLite files remain in ignored `data/`.
`benchmark-results.json` retains all timings and component metrics; benchmarks.csv
is its flat summary. Serialization, reload, fingerprinting and continuation checks
are outside the timed simulation loop. First saves create fresh targets; repeated
saves follow another 30 ticks. Each job then reloads and checks a further 20 ticks.
All four paired fingerprints must match. Exact mature-state comparisons separately
check every field at offsets 0,1,50,200. These are continuation tests, not duplicated
full 100,000-tick lifetimes. The original seed-2026 20,100-tick digest is checked by
the unchanged long-run regression.

## Fingerprints and timing scopes

Streaming fingerprints cover the full header including RNG and scheduler, ordered
cells, every agent field and memory, ancestry, relationships, learned/visit tables,
and every ordered event. Their encoding differs from World.digest; do not compare
the hexadecimal strings across those two formats. Exact comparisons traverse all
logical fields directly, avoiding a second multi-gigabyte full-state dictionary.

Wall seconds use perf_counter; CPU seconds use process_time. 100% CPU means one
logical CPU, not the 16-thread machine. `load_peak_rss_mib` is process high-water
RSS immediately after loading. `simulation_peak_rss_mib` also includes initial
fingerprinting; `overall_peak_rss_mib` includes saving, reloading and comparisons
with two loaded worlds. They are not isolated heap sizes. File sizes are physical
SQLite bytes; logical state and event history remain equivalent despite encoding
and integrity-table differences.

New save metrics split agent fields, ancestry, memory and relationship preparation
plus checksum serialization; agent SQL and event-prefix serialization/SQL insertion
are separate. Timer calls and checks are included in new production saving, not
subtracted. The reference save profile is instrumented and must not be mistaken
for an unprofiled duration. Memory component timing includes tuple preparation and checksum encoding;
SQL insertion also includes streamed row preparation. Do not add nested
serialization totals to their subcomponents. Original deep-copy stages overlap cumulatively; do not
add cumulative profile times as independent costs.

Observer JSON uses SDL's dummy driver and the actual observer loop. Paused trials
run for two seconds, excluding loading and fingerprints. The saving trial freezes
the mature world while the real writer runs; draws and maximum gaps are measured.
These are automated responsiveness checks, not desktop/GPU frame-rate claims.

## Safety and integrity

New checkpoints retain the schema-1 query tables. SQLite user_version=2 marks
mandatory logical checksum metadata. Old user_version=0 archives get structural,
sequence and original world validation; they have no retroactive cryptographic
integrity guarantee. New readers can load old archives. Old readers can inspect
new tables, but using an old writer to erase the new integrity metadata is rejected
by the new reader. Do not downgrade an active checkpoint with an old application.

All saves use one transaction and FULL synchronous durability. The first write or
an untrusted target is a full replacement. Subsequent reuse requires the same
verified file signature and revision, checked current agent contents (including
dead records), and an unchanged complete event prefix. External edits or divergent
history force replacement. Hashing the entire history still costs time. No records
are pruned beyond the original 64-episode rule.

Loads pin a single transaction. A hot rollback journal allows existing-file
read/write recovery; missing paths never create files. The SIGKILL test forces page
spill before killing the writer, then requires the previous complete state and
continuation. Corruption tests cover truncation, cells, event details, memory gaps,
header changes and missing integrity metadata. Corruption after a successful commit
requires an independent backup; no automatic repair or unlimited retention is
claimed. SQLite durability depends on the filesystem/hardware honoring sync.

## Preliminary failures

The defect log and validation logs retain initial failures and corrections.
`pre-hardening-*` and `pre-fk-*` files, exact draft sources and ignored partial data describe the stopped preliminary
benchmark. Those timings are not the final accepted campaign. Final benchmark
source hashes identify the actual implementation measured.

## Final evidence bundle

After the final checks, `python -m research.phase3_package` bundles code, CSV/JSON,
profiles, plots, logs and source snapshots. `phase3-engineering.zip` excludes
large SQLite files; `checkpoint-sha256.txt` records their retained local bytes.
The new-file and repeated-file metrics have different scopes. The final observer
refinement was measured after the headless pass; its separate manifest and the
explicit untimed-source differences preserve that provenance. Timed engine, model,
storage and headless harness hashes must still match strictly.

```bash
sha256sum -c research/phase3/SHA256SUMS.txt
python3 -m zipfile -e research/phase3/phase3-engineering.zip /tmp/gnome-phase3-evidence
cd /tmp/gnome-phase3-evidence
sha256sum -c research/phase3/CONTENTS.sha256
```

The extraction contains support modules and test code, but historical SQLite inputs
remain in the preserved local project or must be regenerated at their original tag.
Wall-clock times, RSS and SQLite byte layouts are environment-dependent; full
logical state, RNG and event outcomes are the equivalence criteria.
