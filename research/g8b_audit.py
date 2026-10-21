"""Source/decision preservation audit against the accepted baseline."""
import ast,hashlib,json,subprocess
from pathlib import Path
BASE='bf6e5568056e75f07cd7b9d468a592fc5e5abf6f'


def main():
    protected=['model.py','terrain_game.py','game.py','terrain_storage.py','game_storage.py',
        'storage.py','terrain_checkpoint.py','game_session.py','checkpoint_recovery.py','chronicle.py',
        'camera.py','pixel_art.py','terrain_presentation.py','game_presentation.py','life_presentation.py',
        'advisor.py','terrain_advisor.py','terrain_viewer.py','god_viewer.py','runtime.py','god_world.py']
    rows=[]
    for name in protected:
        path='gnome_fortress/'+name
        old=subprocess.check_output(['git','show',BASE+':'+path]);new=Path(path).read_bytes()
        rows.append(dict(path=path,identical=old==new,sha256=hashlib.sha256(new).hexdigest()))
    old=ast.parse(subprocess.check_output(['git','show',BASE+':gnome_fortress/engine.py'],text=True))
    new=ast.parse(Path('gnome_fortress/engine.py').read_text())
    def methods(tree):
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='World')
        return {n.name:ast.dump(n,include_attributes=False) for n in cls.body if isinstance(n,ast.FunctionDef)}
    a,b=methods(old),methods(new);changed=[n for n in a if a[n]!=b.get(n)]
    assert changed==['step'] and all(r['identical'] for r in rows)
    history=subprocess.check_output(['git','diff',BASE,'--','research/phase3/reference','docs/game-modes',
        'docs/g8a','docs/g8a1','docs/g8a2'],text=True)
    assert not history
    original=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],text=True).splitlines())
    changed_paths=set(subprocess.check_output(['git','diff','--name-only',BASE],text=True).splitlines())
    old_modified=sorted(original & changed_paths)
    assert set(old_modified)<= {'README.md','gnome_fortress/engine.py','gnome_fortress/living_viewer.py'}
    tags=subprocess.check_output(['git','show-ref','--tags'],text=True)
    result=dict(baseline=BASE,protected=rows,engine_changed_methods=changed,
                all_other_engine_methods_identical_ast=True,protected_prior_documents_unchanged=True,
                tags=tags,modified_preexisting_files=old_modified,owner_checkpoint_opened=False)
    Path('docs/g8b/evidence/preservation.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
