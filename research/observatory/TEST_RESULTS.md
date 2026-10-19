# Verification commands

Run from the repository root with `.venv/bin/python`.

Initial focused command:

```bash
.venv/bin/python -m pytest -q tests/test_observatory.py tests/test_storage.py tests/test_viewer.py tests/test_background.py tests/test_background_cli.py
```

First attempt: 24 passed, 1 test-fixture failure (documented in REPORT.md).
After correction and incremental tests: 26 passed in 3.38 s; later 27 passed
in 3.29 s. Final observatory-only suite, including actual PTY loading/resize:
**16 passed in 2.63 s**.

Existing research controls:

```bash
.venv/bin/python -m pytest -q research/test_analysis.py research/test_phase2.py research/test_study.py
```

**25 passed in 62.82 s** (`research-tests.log`).

Fast regression (excludes the prolonged unattended test):

```bash
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
```

Before final UI hardening: 60 passed in 60.11 s. Final result: **62 passed in
61.73 s**, including all 16 observatory tests (`regression-tests.log`). Combined
with the 25 research tests, **87 tests passed**. The one existing prolonged
unattended test was deliberately excluded; no historical archive campaign was launched.

`integrity-check.json` verifies all seven existing package files against the exact
Phase 3 commit and checks the archived source hash after actual terminal use.
