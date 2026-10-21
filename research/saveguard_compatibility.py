"""Generate legacy saves with the accepted G7 source, then verify current readers."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

from gnome_fortress.game_storage import load_game as load_legacy,save_game as save_legacy
from gnome_fortress.terrain_storage import load_game,save_game

BASELINE='df3a3674fb19104f4be1a0a87c72aabd7474ad16'


def main():
    with tempfile.TemporaryDirectory(prefix='saveguard-legacy-') as folder:
        folder=Path(folder)
        archive=subprocess.check_output(['git','archive',BASELINE,'gnome_fortress'])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:tar.extractall(folder,filter='data')
        script='''import json
from pathlib import Path
from gnome_fortress.game import GameWorld
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.game_storage import save_game as oldsave,load_game as oldload
from gnome_fortress.terrain_storage import save_game,load_game
results={}
for name,cls,write,read in [('legacy',GameWorld,oldsave,oldload),('terrain',TerrainWorld,save_game,load_game)]:
 p=Path(name+('.g1.sqlite' if name=='legacy' else '.g5.sqlite'))
 w=cls(7);w.step(9);w.request('rain',2,2,duration=100);w.request('drought',3,3,duration=40)
 if name=='terrain':w.request('rupture',5,5);w.step();w.request('rewild',5,5)
 write(w,p);initial=w.digest();w.step(60)
 results[name]={'initial_digest':initial,'continuation_digest':w.digest()}
Path('expected.json').write_text(json.dumps(results))
'''
        subprocess.run([sys.executable,'-c',script],cwd=folder,check=True,capture_output=True)
        expected=json.loads((folder/'expected.json').read_text());result={}
        for name,reader,writer,suffix in [('legacy',load_legacy,save_legacy,'g1'),('terrain',load_game,save_game,'g5')]:
            path=folder/f'{name}.{suffix}.sqlite';raw=path.read_bytes();w=reader(path)
            assert hashlib.sha256(raw).digest()==hashlib.sha256(path.read_bytes()).digest()
            assert w.digest()==expected[name]['initial_digest']
            writer(w,path) # same-tick rewrite stays readable by the actual baseline
            probe=f'from gnome_fortress.{"game_storage" if name=="legacy" else "terrain_storage"} import load_game;print(load_game("{path.name}").digest())'
            old_digest=subprocess.check_output([sys.executable,'-c',probe],cwd=folder,text=True).strip()
            assert old_digest==expected[name]['initial_digest']
            w.step(60);assert w.digest()==expected[name]['continuation_digest']
            result[name]={**expected[name],'baseline_reader_after_current_write':True,'unchanged_by_read':True,'exact_continuation':True,'source_sha256':hashlib.sha256(raw).hexdigest()}
        print(json.dumps(dict(generated_by_baseline=BASELINE,results=result),indent=2))


if __name__=='__main__':main()
