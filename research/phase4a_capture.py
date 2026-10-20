"""Real terminal capture of a socially informed living descendant in the pilot."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import struct
import subprocess
import termios
import time

from gnome_fortress.communication import load_experiment
from gnome_fortress.observatory import Observation


def main():
    root = Path(__file__).resolve().parents[1]
    directory = root / 'research/phase4a'
    checkpoint = directory / 'results/pilot-01-social.sqlite'
    before = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    world = load_experiment(checkpoint)
    child = min((a for a in world.living() if a.parents and
                 world.origins.get(a.id, {}).get('move:hazard', {}).get('social_count', 0) and
                 not world.origins[a.id]['move:hazard']['firsthand_count']), key=lambda a:a.id)
    view = Observation(world, live=False); view.select_population('descendants')
    view.selected = view.roster.index(child.id)
    (directory / 'unexposed-descendant-persona.txt').write_text('\n'.join(view.persona())+'\n')
    view.offset = 34
    (directory / 'unexposed-descendant-screen.txt').write_text('\n'.join(view.layout(140,35))+'\n')
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH',35,140,0,0))
    process = subprocess.Popen([str(root/'.venv/bin/python'), '-m', 'gnome_fortress.observatory',
                                '--communication','social','--checkpoint',str(checkpoint)],
                               cwd=root, stdin=slave, stdout=slave, stderr=slave,
                               env={**os.environ,'TERM':'xterm-256color'})
    os.close(slave)
    data = bytearray()

    def collect(seconds):
        end = time.monotonic()+seconds
        while time.monotonic()<end:
            if select.select([master],[],[],.05)[0]:
                try: chunk = os.read(master,65536)
                except OSError: break
                if not chunk: break
                data.extend(chunk)
    try:
        end = time.monotonic()+10
        while b'60 original founders' not in data and time.monotonic()<end:
            collect(.1)
        assert b'60 original founders' in data, 'Checkpoint observer failed to load'
        os.write(master,b'l'); collect(.15)
        os.write(master,b'\t'*view.selected); collect(.07*view.selected+.2)
        os.write(master,b'\x1b[6~'); collect(.2)
        os.write(master,b'\x1b[6~'); collect(.2)
        os.write(master,b'q'); collect(.2)
        code = process.wait(timeout=5)
        assert code==0 and b'Traceback' not in data and b'KNOWLEDGE ORIGINS' in data
        (directory/'descendants-terminal.ansi').write_bytes(data)
        after = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        assert before==after
        (directory/'terminal-check.json').write_text(json.dumps(dict(exit_code=code, selected_id=child.id,
            parents=child.parents, tick=world.tick, origin=world.origins[child.id]['move:hazard'],
            source_unchanged=True, source_sha256=before, capture_bytes=len(data)),indent=2)+'\n')
    finally:
        if process.poll() is None: process.kill(); process.wait()
        os.close(master)


if __name__=='__main__':
    main()
