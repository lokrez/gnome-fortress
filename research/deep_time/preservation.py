"""Read-only artifact audit under the existing shared owner/writer gates."""
import fcntl,hashlib,json,os,sqlite3,subprocess
from contextlib import ExitStack,closing
from pathlib import Path


def main():
 root=Path(__file__).resolve().parents[2];out=root/'docs/deep-time/evidence'
 original=json.loads((out/'artifact-preservation.json').read_text());path=Path(original['source'])
 with ExitStack() as stack:
  for suffix in ('.lock','.writer.lock'):
   handle=stack.enter_context(open(str(path)+suffix,'rb'));fcntl.flock(handle,fcntl.LOCK_SH|fcntl.LOCK_NB)
  before=path.stat()
  with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
   db.execute('BEGIN');metadata=db.execute('SELECT id,format,sha256,length(CAST(payload AS BLOB)) FROM game_checkpoint').fetchone()
   sha=hashlib.sha256()
   with db.blobopen('game_checkpoint','payload',1,readonly=True) as blob:
    while data:=blob.read(8*1024*1024):sha.update(data)
   assert sha.hexdigest()==metadata[2]==original['sha256']
  assert path.stat().st_mtime_ns==before.st_mtime_ns==original['source_mtime_ns']
  assert path.stat().st_size==before.st_size==original['source_bytes']
 # Private rewritten copy must contain precisely the original canonical payload.
 with closing(sqlite3.connect(Path(original['copy']).as_uri()+'?mode=ro',uri=True)) as db:
  db.execute('BEGIN');private_sha=db.execute('SELECT sha256 FROM game_checkpoint').fetchone()[0]
  sha=hashlib.sha256()
  with db.blobopen('game_checkpoint','payload',1,readonly=True) as blob:
   while data:=blob.read(8*1024*1024):sha.update(data)
  assert sha.hexdigest()==private_sha==original['sha256']
 changed=subprocess.check_output(['git','diff','--name-only','72a1017','--','gnome_fortress'],cwd=root,text=True).splitlines()
 assert set(changed)<= {'gnome_fortress/terrain_storage.py','gnome_fortress/terrain_encoding.py','gnome_fortress/god_world.py'},changed
 assert 'gnome_fortress/terrain_storage.py' in changed
 protected=('engine.py','model.py','chronicle.py','terrain_checkpoint.py','game_session.py','checkpoint_recovery.py',
  'game.py','terrain_game.py','living_viewer.py','pixel_art.py','camera.py','god_viewer.py','decision_observation.py')
 source_hashes={}
 for name in protected:
  name='gnome_fortress/'+name
  old=subprocess.check_output(['git','show','72a1017:'+name],cwd=root)
  assert (root/name).read_bytes()==old,name
  source_hashes[name]=hashlib.sha256(old).hexdigest()
 data=dict(source=original['source'],payload_sha256=original['sha256'],payload_bytes=metadata[3],source_bytes=before.st_size,
   source_unchanged=True,private_rewrite_payload_identical=True,source_mtime_ns=before.st_mtime_ns,
   protected_sources=source_hashes,changed_existing_production=changed,
   tags=subprocess.check_output(['git','show-ref','--tags'],cwd=root,text=True).splitlines())
 (out/'preservation.json').write_text(json.dumps(data,indent=2)+'\n');print('Protected artifact and private canonical bytes exact; protected sources unchanged.')

if __name__=='__main__':main()
