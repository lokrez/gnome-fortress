"""Protected source/artifact audit, nonblocking shared owner and writer gates."""
import fcntl,hashlib,json,sqlite3,subprocess
from contextlib import ExitStack,closing
from pathlib import Path


def main():
 root=Path(__file__).resolve().parents[2];out=root/'docs/g8c/evidence'
 first=json.loads((out/'preservation-start.json').read_text());path=Path(first['source'])
 with ExitStack() as stack:
  for suffix in ('.lock','.writer.lock'):
   f=stack.enter_context(open(str(path)+suffix,'rb'));fcntl.flock(f,fcntl.LOCK_SH|fcntl.LOCK_NB)
  st=path.stat();assert st.st_size==first['source_bytes'] and st.st_mtime_ns==first['source_mtime_ns']
  with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
   db.execute('BEGIN');sha=hashlib.sha256()
   with db.blobopen('game_checkpoint','payload',1,readonly=True) as blob:
    while data:=blob.read(8*1024*1024):sha.update(data)
   assert sha.hexdigest()==db.execute('SELECT sha256 FROM game_checkpoint').fetchone()[0]==first['hashes']['protected']
 allowed={'gnome_fortress/chronicle.py','gnome_fortress/chronicle_index.py','gnome_fortress/terrain_checkpoint.py','gnome_fortress/god_viewer.py','gnome_fortress/terrain_encoding.py'}
 changed=subprocess.check_output(['git','diff','--name-only','c88b217'],cwd=root,text=True).splitlines()
 assert all(p in allowed or p.startswith(('docs/g8c/','research/g8c/','tests/test_g8c_')) for p in changed),changed
 files=subprocess.check_output(['git','ls-tree','-r','--name-only','c88b217','gnome_fortress'],cwd=root,text=True).splitlines();protected={}
 for p in files:
  if p in allowed:continue
  original=subprocess.check_output(['git','show','c88b217:'+p],cwd=root)
  assert (root/p).read_bytes()==original,p;protected[p]=hashlib.sha256(original).hexdigest()
 tags=subprocess.check_output(['git','show-ref','--tags'],cwd=root,text=True).splitlines()
 baseline=json.loads(subprocess.check_output(['git','show','c88b217:docs/deep-time/evidence/preservation.json'],cwd=root))
 assert tags==baseline['tags']
 # Strict storage and its full previous validation must remain byte-identical.
 for p in ('gnome_fortress/terrain_storage.py','gnome_fortress/game_session.py','gnome_fortress/checkpoint_recovery.py'):
  assert p in protected
 result=dict(protected_payload_sha256=sha.hexdigest(),source_size=st.st_size,source_mtime_ns=st.st_mtime_ns,
             original_untouched=True,protected_sources=protected,changed=changed,tags_unchanged=True,tags=tags)
 (out/'preservation-final.json').write_text(json.dumps(result,indent=2)+'\n');print('Protected checkpoint, strict storage, simulation, gameplay, art and historical tags unchanged.')

if __name__=='__main__':main()
