import json
import os
import signal
import subprocess
import sys
import time

from gnome_fortress.engine import World
from gnome_fortress.storage import load


def invoke(path, ticks, *extra, hash_seed="1"):
    env = dict(os.environ, PYTHONHASHSEED=hash_seed)
    result = subprocess.run([sys.executable, "-m", "gnome_fortress", "--headless",
                             "--db", str(path), "--ticks", str(ticks), *extra],
                            capture_output=True, text=True, check=True, env=env)
    return json.loads(result.stdout)


def test_cli_resume_and_hash_seed_independence(tmp_path):
    a, b = tmp_path / "a.sqlite", tmp_path / "b.sqlite"
    invoke(a, 30, "--seed", "2026")
    resumed = invoke(a, 30, hash_seed="999")
    whole = invoke(b, 60, "--seed", "2026", hash_seed="24")
    assert resumed["digest"] == whole["digest"]
    assert load(a).digest() == load(b).digest()


def test_sigint_saves_only_complete_ticks(tmp_path):
    path = tmp_path / "interrupt.sqlite"
    process = subprocess.Popen([sys.executable, "-m", "gnome_fortress", "--headless",
                                "--db", str(path), "--ticks", "200000", "--checkpoint-every", "20"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 15
        while not path.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert path.exists()
        process.send_signal(signal.SIGINT)
        out, err = process.communicate(timeout=15)
        assert process.returncode == 0, err
        summary = json.loads(out)
        restored = load(path)
        reference = World(1)
        reference.step(summary["tick"])
        assert reference.digest() == restored.digest() == summary["digest"]
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()
