"""Compact Phase 2 scientific bundle, leaving large SQLite archives local."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT=Path('research/phase2')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def main():
    verification=json.loads((ROOT/'results/verification.json').read_text())
    assert verification['runs']==58 and verification['all_archives_reconciled']
    subprocess.run(['git','diff','--exit-code','f32c1a6','--','gnome_fortress','tests','pyproject.toml','requirements-tested.txt'],check=True)
    subprocess.run(['git','diff','--exit-code','232dd30','--','research/phase1','research/study.py','research/analyze.py','research/verify.py','research/test_study.py','research/test_analysis.py'],check=True)
    # Verify published historical artifact bytes as well as tracked source/history.
    subprocess.run(['sha256sum','-c','research/phase1/SHA256SUMS.txt'],check=True)
    subprocess.run(['sha256sum','-c','research/phase1/checkpoint-sha256.txt'],check=True)
    snapshots=sorted((ROOT/'data').rglob('*.sqlite'))
    (ROOT/'checkpoint-sha256.txt').write_text(''.join(f'{sha(p)}  {p.as_posix()}\n' for p in snapshots))
    provenance=dict(original_commit=subprocess.check_output(['git','rev-parse','phase0-verified'],text=True).strip(),
                    phase1_commit=subprocess.check_output(['git','rev-parse','phase1-verified'],text=True).strip(),
                    experiment_controls_commit='1e67c3e',source_and_phase1_unchanged=True,
                    runs=58,local_sqlite_snapshots=len(snapshots),
                    code_sha256={str(p):sha(p) for p in sorted(Path('research').glob('phase2_*.py'))},
                    original_engine_sha256={str(p):sha(p) for p in sorted(Path('gnome_fortress').glob('*.py'))},
                    note='Bundle contains CSV/JSON, figures, logs and experiment code; SQLite snapshots remain local or can be regenerated.')
    (ROOT/'REPRODUCIBILITY.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    archive=ROOT/'phase2-study.zip'
    excluded={archive,ROOT/'CONTENTS.sha256',ROOT/'SHA256SUMS.txt'}
    files=sorted(p for p in ROOT.rglob('*') if p.is_file() and p not in excluded and
                 '.sqlite' not in p.name and '__pycache__' not in p.parts and p.suffix!='.pyc')
    files+=sorted(Path('research').glob('phase2_*.py'))
    files+=[Path('research/test_phase2.py'),Path('research/requirements-tested.txt')]
    # Include the three historical population prefixes needed to redraw endurance figures.
    for seed in (1,2,3):
        files.extend(Path(f'research/phase1/data/seed-{seed:02d}')/name for name in ('population.csv','summary.json'))
    files=sorted(set(files))
    (ROOT/'CONTENTS.sha256').write_text(''.join(f'{sha(p)}  {p.as_posix()}\n' for p in files))
    files.append(ROOT/'CONTENTS.sha256')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for path in sorted(files):
            item=zipfile.ZipInfo(path.as_posix(),date_time=(2026,10,19,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o644<<16
            bundle.writestr(item,path.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None and len(bundle.namelist())==len(files)
    (ROOT/'SHA256SUMS.txt').write_text(f'{sha(archive)}  {archive.as_posix()}\n{sha(ROOT/"CONTENTS.sha256")}  {(ROOT/"CONTENTS.sha256").as_posix()}\n')
    print(json.dumps(dict(files=len(files),bytes=archive.stat().st_size,sha256=sha(archive)),indent=2))


if __name__=='__main__':
    main()
