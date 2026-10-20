# Gate 1 — versioned terrain gameplay foundation

Separate TerrainWorld subclass and launcher:

```bash
.venv/bin/python -m gnome_fortress.god_world --new --db run-results/god-terrain/my-world.g5.sqlite
```

The new default is `run-results/god-terrain/world.g5.sqlite`; an existing valid
terrain world resumes. `--new` requires an unused destination. Original
`python -m gnome_fortress.god_demo` and `.g1.sqlite` saves remain operational.

Explicit copy-only import:

```bash
.venv/bin/python -m gnome_fortress.god_world --import-legacy run-results/god/world.g1.sqlite --db run-results/god-terrain/imported.g5.sqlite --paused
```

Format `gnome-fortress-terrain-g5-v1`, record version 1, SQLite application ID
`0x474E4735`, schema 1, `.g5.sqlite` suffix. All simulation state/RNG, initial
terrain at format epoch, intervention records and explicit import provenance are
stored in a checksummed canonical JSON snapshot. Legacy source is read-only;
new origin records source format, tick and full legacy digest. Import does not
claim the old world always had terrain powers. There is no in-place upgrade.

New files are built transactionally in the target directory then published using
an exclusive hard link, refusing existing/racing destinations. Existing updates
use FULL synchronous SQLite transactions and verify the previous snapshot before
writing. Unsupported/corrupt databases fail closed. Research paths/suffixes are
protected. This is not Ironman or recovery journaling; unsaved requests/ticks can
be lost on crash. Single writer per checkpoint remains required.

Gate 1 executed evidence: [focused tests](foundation-tests.txt) and bounded
[CLI new/resume demonstration](foundation-demo.txt). Tests cover exact state/RNG,
legacy bytes, original reader, copy-import, active Rain/Drought, matching no-power
reference, continuation, interrupted SQL update rollback, checksum/version/
incomplete-file rejection and exclusive publication races. Existing game and G2
presentation tests are included. No historical archive campaign.
