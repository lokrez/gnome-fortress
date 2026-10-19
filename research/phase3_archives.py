"""Preserve historical bytes and load every published historical SQLite archive."""
import ast,gc,hashlib,json,subprocess
from pathlib import Path
from gnome_fortress import engine
from gnome_fortress.storage import load
from research.phase2_controls import Config,capacity,load_experiment

ROOT=Path('research/phase3')


def main():
    ref='5efc9b1bfdd8d49a13aefd4e9256e6c1e87c024f'
    original=subprocess.check_output(['git','ls-tree','-r','--name-only',ref,'research','tests'],text=True).splitlines()
    for name in original:
        assert Path(name).read_bytes()==subprocess.check_output(['git','show',f'{ref}:{name}']),name
    tags={'phase0-verified':'f32c1a612e36b046faa501273640bbabfce5159d',
          'phase1-verified':'232dd30ce56a4d3645efb3d1dc35cd0539deb497','phase2-verified':ref}
    for tag,expected in tags.items():assert subprocess.check_output(['git','rev-parse',tag],text=True).strip()==expected
    reference=json.loads((ROOT/'reference/SOURCE.json').read_text())
    for name,digest in reference['files'].items():
        data=(ROOT/'reference'/name).read_bytes()
        assert data==subprocess.check_output(['git','show',f'{ref}:gnome_fortress/{name}'])
        assert hashlib.sha256(data).hexdigest()==digest
    def methods(path):
        tree=ast.parse(Path(path).read_text())
        return {n.name:ast.dump(n,include_attributes=False) for c in tree.body if isinstance(c,ast.ClassDef) and c.name=='World' for n in c.body if isinstance(n,ast.FunctionDef)}
    before,after=methods(ROOT/'reference/engine.py'),methods('gnome_fortress/engine.py')
    unchanged=('decide','move','remember','_biology','observations','neighbors','_drinkable')
    assert all(before[name]==after[name] for name in unchanged)
    assert Path('gnome_fortress/model.py').read_bytes()==(ROOT/'reference/model.py').read_bytes()
    assert engine.SLOTS==60
    files=[]
    for phase in ('phase1','phase2'):
        subprocess.run(['sha256sum','-c',f'research/{phase}/SHA256SUMS.txt'],check=True,stdout=subprocess.DEVNULL)
        manifest=Path(f'research/{phase}/checkpoint-sha256.txt')
        subprocess.run(['sha256sum','-c',str(manifest)],check=True,stdout=subprocess.DEVNULL)
        files += [Path(line.split('  ',1)[1]) for line in manifest.read_text().splitlines()]
    outputs=[]
    for path in files:
        sidecar=path.with_suffix('.config.json')
        if sidecar.exists():
            cfg=Config(**json.loads(sidecar.read_text()))
            with capacity(cfg.slots):w=load_experiment(path,cfg)
        else:w=load(path)
        expected=None
        summary=path.with_name('summary.json')
        if path.name=='final.sqlite' and summary.exists():expected=json.loads(summary.read_text())['final_digest']
        if path.name.startswith('checkpoint-'):
            tick=int(path.stem.split('-')[-1])
            expected=next(c['state_digest'] for c in json.loads(path.with_name('checkpoints.json').read_text()) if c['tick']==tick)
        if path.name=='snapshot-probe.sqlite':expected=json.loads(path.with_name('case-5.json').read_text())['final_digest']
        assert expected is not None,path
        digest=w.digest()
        assert digest==expected,path
        outputs.append(dict(path=str(path),tick=w.tick,exact_published_digest=bool(expected),digest=digest))
        print('LOADED HISTORICAL',path,flush=True)
        del w;gc.collect()
    current=json.loads((ROOT/'benchmark-manifest.json').read_text())
    differences={p:dict(measured=h,final=hashlib.sha256(Path(p).read_bytes()).hexdigest())
        for p,h in current['code_hashes'].items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h}
    allowed={'gnome_fortress/viewer.py','research/phase3_observer.py','research/phase3_archives.py'}
    assert set(differences)<=allowed,differences
    observed=json.loads((ROOT/'observer-manifest.json').read_text())
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in observed['code_hashes'].items())
    (ROOT/'historical-verification.json').write_text(json.dumps(dict(tags=tags,original_tests_and_research_unchanged=True,
        timed_headless_sources_match=True,post_headless_observer_changes=differences,observer_source_hashes_match=True,unchanged_rule_methods=unchanged,archives=outputs),indent=2)+'\n')
    print('HISTORICAL BYTE AND LOAD VERIFICATION COMPLETE',len(outputs),flush=True)

if __name__=='__main__':main()
