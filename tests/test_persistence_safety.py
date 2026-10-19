import json,os,signal,sqlite3,subprocess,sys,time
import pytest
from gnome_fortress.engine import World
from gnome_fortress.storage import load,save
from research.phase3.reference import storage as reference


def test_legacy_upgrade_incremental_and_old_reader(tmp_path):
    path=tmp_path/'state.sqlite'; w=World(42); w.step(100)
    reference.save(w,path)
    restored=load(path); assert restored.state()==w.state()
    first=save(restored,path); assert not first['incremental']
    n=len(restored.events); restored.step(30)
    second=save(restored,path)
    assert second['incremental'] and second['events_written']==len(restored.events)-n
    assert load(path).state()==reference.load(path).state()==restored.state()
    reference.save(restored,path)  # An old writer must not silently strip integrity.
    with pytest.raises(ValueError,match='integrity'):load(path)


def test_dead_mutations_and_divergent_prefix_are_not_lost(tmp_path):
    path=tmp_path/'state.sqlite'; w=World(); w.step(200)
    a=w.living()[0]; w.kill(a,'test'); save(w,path)
    a.learned['probe']=7; a.relationships[2]=3; a.memories[-1].reward+=1
    changed=save(w,path)
    assert changed['incremental'] and changed['agents_written']==1
    assert load(path).state()==w.state()
    w.events[0].detail['probe']=True
    replaced=save(w,path)
    assert not replaced['incremental'] and load(path).state()==w.state()


@pytest.mark.parametrize('damage',['cell','event','memory','header','integrity','truncated'])
def test_corruption_rejected(tmp_path,damage):
    p=tmp_path/'corrupt.sqlite'; w=World();w.step(100);save(w,p)
    if damage=='truncated':
        with p.open('r+b') as f:f.truncate(p.stat().st_size//2)
    else:
        with sqlite3.connect(p) as db:
            if damage=='cell':db.execute('UPDATE cells SET food=food+1 WHERE x=1 AND y=1')
            elif damage=='event':db.execute("UPDATE events SET detail='{}' WHERE sequence=0")
            elif damage=='memory':db.execute('DELETE FROM memories WHERE sequence=1')
            elif damage=='integrity':db.execute("DELETE FROM metadata WHERE key='integrity'")
            elif damage=='header':
                d=json.loads(db.execute("SELECT value FROM metadata WHERE key='world'").fetchone()[0])
                d['tick']+=1
                db.execute("UPDATE metadata SET value=? WHERE key='world'",(json.dumps(d),))
    with pytest.raises((ValueError,sqlite3.Error)):load(p)


def test_external_edit_invalidates_incremental_reuse(tmp_path):
    p=tmp_path/'edited.sqlite';w=World();w.step(100);save(w,p)
    with sqlite3.connect(p) as db:db.execute('UPDATE cells SET food=0')
    result=save(w,p)
    assert not result['incremental'] and load(p).state()==w.state()


def test_sigkill_mid_transaction_recovers_last_committed_tick(tmp_path):
    p=tmp_path/'crash.sqlite'; marker=tmp_path/'ready';w=World();w.step(200);save(w,p)
    before=w.digest()
    with sqlite3.connect(p) as db:
        db.execute('CREATE TRIGGER block_save BEFORE INSERT ON events BEGIN SELECT pause_write(); END')
    script='''import pathlib,sqlite3,sys,time
from gnome_fortress import storage
original=sqlite3.connect
def connect(*args,**kwargs):
 db=original(*args,**kwargs);db.execute('PRAGMA cache_size=8')
 def block():
  pathlib.Path(sys.argv[2]).write_text('ready');time.sleep(30);return 0
 db.create_function('pause_write',0,block);return db
storage.sqlite3.connect=connect
w=storage.load(sys.argv[1]);w.step(30);storage.save(w,sys.argv[1])
'''
    process=subprocess.Popen([sys.executable,'-c',script,str(p),str(marker)],stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+15
        while not marker.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.01)
        assert marker.exists(),process.communicate(timeout=1) if process.poll() is not None else 'writer timeout'
        journal=p.with_name(p.name+'-journal')
        assert journal.exists() and journal.stat().st_size>512
        process.kill();process.communicate(timeout=5)
        restored=load(p)
        assert restored.digest()==before
        restored.step(30);w.step(30);assert restored.state()==w.state()
    finally:
        if process.poll() is None:process.kill();process.communicate()


def test_header_checksum_precedes_materialization(tmp_path,monkeypatch):
    p=tmp_path/'bad-header.sqlite';save(World(),p)
    with sqlite3.connect(p) as db:
        data=json.loads(db.execute("SELECT value FROM metadata WHERE key='world'").fetchone()[0])
        data['width']=10**12
        db.execute("UPDATE metadata SET value=? WHERE key='world'",(json.dumps(data),))
    called=[]
    def forbidden(*args,**kwargs):
        called.append(True);raise RuntimeError('Corrupt dimensions reached materialization')
    monkeypatch.setattr(World,'from_state',forbidden)
    with pytest.raises(ValueError,match='header'):load(p)
    assert not called
