"""Bundle verified engineering evidence, leaving SQLite states available locally."""
import hashlib,json,re,zipfile
from pathlib import Path
ROOT=Path('research/phase3')


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(1024*1024):h.update(block)
    return h.hexdigest()


def main():
    history=json.loads((ROOT/'historical-verification.json').read_text())
    assert len(history['archives'])==72 and all(r['exact_published_digest'] for r in history['archives'])
    assert history['timed_headless_sources_match'] and history['observer_source_hashes_match']
    log=(ROOT/'validation/final-regression.log').read_text()
    assert '72 passed' in log and '18abcc54608881c6892e1b913cd2b56d6288068afb4515f3467e94cab3c9696e' in log
    rows=json.loads((ROOT/'benchmark-results.json').read_text());assert len(rows)==10
    for name in {r['name'] for r in rows}:
        pair=[r for r in rows if r['name']==name];assert len(pair)==2
        for key in ('initial_digest','after_loop_digest','final_digest','continuation_digest'):
            assert pair[0][key]==pair[1][key]
    states=sorted((ROOT/'data').glob('*/*/checkpoint.sqlite'))
    states += [p for p in (ROOT/'data').glob('*.sqlite') if not p.name.startswith('pre-')]
    (ROOT/'checkpoint-sha256.txt').write_text(''.join(f'{sha(p)}  {p}\n' for p in states))
    sources=sorted(list(Path('gnome_fortress').glob('*.py'))+list(Path('research').glob('phase3_*.py')))
    (ROOT/'REPRODUCIBILITY.json').write_text(json.dumps(dict(reference=history['tags']['phase2-verified'],
        final_tag='phase3-verified',tested_rule_equivalence=True,tests=72,historical_archives=72,
        code_sha256={str(p):sha(p) for p in sources},
        note='SQLite files remain local. Complete logical histories reproduce from preserved inputs and fixed tick counts.'),indent=2,sort_keys=True)+'\n')
    archive=ROOT/'phase3-engineering.zip'
    excluded={archive,ROOT/'CONTENTS.sha256',ROOT/'SHA256SUMS.txt'}
    files=[p for p in ROOT.rglob('*') if p.is_file() and p not in excluded and 'data' not in p.relative_to(ROOT).parts
           and '__pycache__' not in p.parts and p.suffix!='.pyc' and '.sqlite' not in p.name]
    files+=list(Path('gnome_fortress').glob('*.py'))+list(Path('research').glob('*.py'))+list(Path('tests').glob('*.py'))
    files += [Path(p) for p in ('README.md','ARCHITECTURE.md','VERIFICATION.md','pyproject.toml','requirements-tested.txt','research/requirements-tested.txt')]
    # Preserve accepted raw records and diagnostic results, without large databases.
    files += list((ROOT/'data').rglob('result.json'))
    files=sorted(set(files))
    (ROOT/'CONTENTS.sha256').write_text(''.join(f'{sha(p)}  {p}\n' for p in files))
    files.append(ROOT/'CONTENTS.sha256')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(files):
            info=zipfile.ZipInfo(str(p),date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
            z.writestr(info,p.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    (ROOT/'SHA256SUMS.txt').write_text(f'{sha(archive)}  {archive}\n{sha(ROOT/"CONTENTS.sha256")}  {ROOT/"CONTENTS.sha256"}\n')
    print(json.dumps(dict(files=len(files),bytes=archive.stat().st_size,sha256=sha(archive)),indent=2))

if __name__=='__main__':main()
