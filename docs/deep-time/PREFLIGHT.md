# Operation Deep Time — preflight

Starting revision: 72a101727d84a65dd49186503eea765825fa0987; clean main.
Campaign branch: feature/deep-time. Remote: git@github.com:lokrez/gnome-fortress.git.
No active/suspended god_world or god_demo process found. Disk: about 49 GiB free.

Protected player artifact: run-results/god-terrain/world.g5.sqlite.
Recorded canonical SHA-256:
865f2d2304e3e302650860c25ddbae88d06ecc80323da61f0414bce7682a2611.
The existing October 21 read-only analysis and clean shutdown agree on that hash.
The local report is run-results/reports/2026-10-21-life-observed/REPORT.md.
No player-world execution, mutation, migration, overwriting or history pruning is permitted.

Plan: one independent benchmark copy under /tmp (never a hard link), reused for
benchmark reads and writes; it has an independent identity from the protected source.
Copying the closed artifact uses shared existing ownership/writer gates. Check
inode separation and checksum. Keep old reports, research data and tags unchanged.
At most a few gigabytes of temporary database copies; inspect disk before growth.

Boundaries: original engine/model decisions, experimental Phase 4 controls, art,
camera, G8B, Saveguard lifetime/flock/orphan gates, format/schema/checksums/FULL-sync
and all objective history remain authoritative. Performance work precedes science.
No G9 or new gameplay. Record gate results and separate meaningful commits.
