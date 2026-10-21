import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import subprocess
import signal
import sys
import time
from pathlib import Path

from gnome_fortress.game_session import game_session
from gnome_fortress.terrain_storage import load_game


def test_busy_launcher_refuses_before_touching_database(tmp_path):
    path=tmp_path/'busy.g5.sqlite'
    with game_session(path):
        result=subprocess.run([sys.executable,'-m','gnome_fortress.god_world','--db',str(path),'--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert result.returncode==2 and 'already in use' in result.stderr and 'suspended' in result.stderr
        assert not path.exists()
    result=subprocess.run([sys.executable,'-m','gnome_fortress.god_world','--db',str(path),'--headless','--ticks','0'],capture_output=True,timeout=5)
    assert result.returncode==0 and load_game(path).tick==0


def test_killed_owner_releases_lock_despite_stale_file(tmp_path):
    path=tmp_path/'killed.g5.sqlite'
    code='from pathlib import Path; from gnome_fortress.game_session import game_session; import sys,time\nwith game_session(Path(sys.argv[1])):\n print("locked",flush=True)\n time.sleep(30)'
    process=subprocess.Popen([sys.executable,'-c',code,str(path)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='locked'
        process.kill();process.wait(timeout=3)
        lock=Path(str(path)+'.lock');assert lock.read_text()==str(process.pid)
        with game_session(path):assert lock.read_text()==str(os.getpid())
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_running_cli_holds_guard_through_clean_shutdown(tmp_path):
    path=tmp_path/'interactive.g5.sqlite';command=[sys.executable,'-m','gnome_fortress.god_world','--db',str(path)]
    process=subprocess.Popen(command+['--paused'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        deadline=time.monotonic()+5
        while not path.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert path.exists() and process.poll() is None
        raw=path.read_bytes()
        second=subprocess.run(command+['--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert second.returncode==2 and 'already in use' in second.stderr and path.read_bytes()==raw
        process.terminate();out,err=process.communicate(timeout=8);assert process.returncode==0,(out,err)
        third=subprocess.run(command+['--headless','--ticks','0'],capture_output=True,timeout=5)
        assert third.returncode==0 and load_game(path).tick==0
    finally:
        if process.poll() is None:process.kill();process.wait()


def test_suspended_owner_still_blocks_second_session(tmp_path):
    path=tmp_path/'suspended.g5.sqlite'
    code='from pathlib import Path; from gnome_fortress.game_session import game_session; import sys,time\nwith game_session(Path(sys.argv[1])):\n print("locked",flush=True)\n time.sleep(30)'
    process=subprocess.Popen([sys.executable,'-c',code,str(path)],stdout=subprocess.PIPE,text=True)
    try:
        assert process.stdout.readline().strip()=='locked'
        process.send_signal(signal.SIGSTOP)
        result=subprocess.run([sys.executable,'-m','gnome_fortress.god_world','--db',str(path),'--headless','--ticks','0'],capture_output=True,text=True,timeout=5)
        assert result.returncode==2 and 'already in use' in result.stderr
        assert not path.exists()
    finally:
        process.kill();process.wait(timeout=3)
