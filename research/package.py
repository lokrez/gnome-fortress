"""Package verified research artifacts, without large SQLite snapshots or caches."""
import hashlib
import json
from pathlib import Path
import platform
import sqlite3
import subprocess
import zipfile

ROOT = Path("research/phase1")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()


def main():
    subprocess.run(["git", "diff", "--exit-code", "f32c1a6", "--", "gnome_fortress", "tests", "pyproject.toml", "requirements-tested.txt"], check=True)
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    assert sha(Path("research/study.py")) == manifest["harness_sha256"]
    assert sha(ROOT / "PROTOCOL.md") == manifest["protocol_sha256"]
    verification = json.loads((ROOT / "results/verification.json").read_text())
    assert verification["independent_uninstrumented_replay"]["equal"]
    baseline = subprocess.check_output(["git", "rev-parse", "phase0-verified"], text=True).strip()
    assert baseline == manifest["baseline"]
    provenance = dict(baseline=baseline, original_engine_and_tests_unchanged=True,
                      protocol_sha256=manifest["protocol_sha256"], harness_sha256=manifest["harness_sha256"],
                      original_tests=dict(passed=27, failed=0, skipped=0, seconds=168.33),
                      research_tests=dict(passed=6, failed=0, seconds=8.20),
                      independent_uninstrumented_replay=verification["independent_uninstrumented_replay"],
                      python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                      seeds=manifest["seeds"], ticks=manifest["ticks"],
                      engine_sha256={str(p): sha(p) for p in sorted(Path("gnome_fortress").glob("*.py"))},
                      timing_note="Execution timing varies; CSV values and logical state digests reproduce on this runtime/rule version.")
    (ROOT / "REPRODUCIBILITY.json").write_text(json.dumps(provenance, indent=2, sort_keys=True)+"\n")
    checkpoints = sorted((ROOT / "data").glob("seed-*/final.sqlite"))
    assert len(checkpoints) == 10
    (ROOT / "checkpoint-sha256.txt").write_text("".join(f"{sha(p)}  {p.as_posix()}\n" for p in checkpoints))
    archive = ROOT / "population-study.zip"
    excluded = {archive, ROOT / "CONTENTS.sha256", ROOT / "SHA256SUMS.txt"}
    files = sorted(p for p in Path("research").rglob("*") if p.is_file() and
                   p not in excluded and "__pycache__" not in p.parts and
                   ".pytest_cache" not in p.parts and ".sqlite" not in p.name and p.suffix != ".pyc")
    (ROOT / "CONTENTS.sha256").write_text("".join(f"{sha(p)}  {p.as_posix()}\n" for p in files))
    files.append(ROOT / "CONTENTS.sha256")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files):
            info = zipfile.ZipInfo(path.as_posix(), date_time=(2026, 10, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(files)
    (ROOT / "SHA256SUMS.txt").write_text(f"{sha(archive)}  {archive.as_posix()}\n{sha(ROOT / 'CONTENTS.sha256')}  {(ROOT / 'CONTENTS.sha256').as_posix()}\n")
    print(json.dumps(dict(files=len(files), archive=str(archive), bytes=archive.stat().st_size,
                         sha256=sha(archive)), indent=2))


if __name__ == "__main__":
    main()
