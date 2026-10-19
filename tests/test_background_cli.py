import json,os,signal,subprocess,sys,time
from gnome_fortress.storage import load
from research.phase3.reference.engine import World as ReferenceWorld


def test_forever_pacing_statistics_and_sigterm(tmp_path):
    p=tmp_path/'background.sqlite'
    process=subprocess.Popen([sys.executable,'-m','gnome_fortress','--headless','--forever',
        '--rate','30','--stats-every','.02','--checkpoint-every','3','--db',str(p)],
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+10
        while not p.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.01)
        assert p.exists();time.sleep(.15);process.send_signal(signal.SIGTERM)
        out,err=process.communicate(timeout=10)
        assert process.returncode==0,err
        result=json.loads(out);w=load(p);ref=ReferenceWorld(1);ref.step(w.tick)
        assert w.tick>=3 and w.digest()==ref.digest()==result['digest']
        assert any(json.loads(line)['kind']=='performance' for line in err.splitlines())
    finally:
        if process.poll() is None:process.kill();process.communicate()


def test_invalid_operational_rate_does_not_create_checkpoint(tmp_path):
    p=tmp_path/'invalid.sqlite'
    result=subprocess.run([sys.executable,'-m','gnome_fortress','--headless','--rate','nan','--db',str(p)],capture_output=True,text=True)
    assert result.returncode!=0 and not p.exists()
