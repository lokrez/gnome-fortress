"""Reproducible real Linux PTY capture, including keys and resize (no UI mocks)."""
import fcntl
import json
import os
from pathlib import Path
import pty
import select
import resource
import struct
import subprocess
import sys
import termios
import time

ROOT = Path(__file__).resolve().parents[2]


def capture(checkpoint=None, output_directory=None, load_timeout=45):
    started = time.monotonic()
    cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH', 35, 140, 0, 0))
    command = [str(ROOT / '.venv/bin/python'), '-m', 'gnome_fortress.observatory']
    if checkpoint:
        command += ['--checkpoint', str(checkpoint)]
    process = subprocess.Popen(command, cwd=ROOT, stdin=slave, stdout=slave, stderr=slave,
                               env={**os.environ, 'TERM': 'xterm-256color'})
    os.close(slave)
    data = bytearray()

    def collect(seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if select.select([master], [], [], .05)[0]:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk: break
                data.extend(chunk)

    try:
        deadline = time.monotonic() + load_timeout
        while b'60 original founders' not in data and time.monotonic() < deadline:
            collect(.2)
        if b'60 original founders' not in data:
            raise RuntimeError(f'Observer did not finish loading within {load_timeout} seconds')
        # Tab selection, single-step, inspector scroll and a real terminal resize.
        os.write(master, b'\t.'); collect(.4)
        os.write(master, b'\x1b[6~'); collect(.3)
        fcntl.ioctl(master, termios.TIOCSWINSZ, struct.pack('HHHH', 18, 60, 0, 0))
        import signal
        process.send_signal(signal.SIGWINCH)
        collect(.4)
        os.write(master, b'q'); collect(.3)
        code = process.wait(timeout=30)
        name = 'checkpoint' if checkpoint else 'fresh'
        output = Path(output_directory or ROOT / 'research/observatory') / f'{name}-terminal.ansi'
        output.write_bytes(data)
        cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = cpu_after.ru_utime + cpu_after.ru_stime - cpu_before.ru_utime - cpu_before.ru_stime
        return dict(mode=name, exit_code=code, capture_bytes=len(data),
                    elapsed_seconds=time.monotonic()-started, cpu_seconds=cpu,
                    traceback=b'Traceback' in data, roster_rendered=b'60 original founders' in data,
                    path=str(output.relative_to(ROOT)) if output.is_relative_to(ROOT) else str(output))
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        os.close(master)


if __name__ == '__main__':
    print(json.dumps(capture(Path(sys.argv[1]) if len(sys.argv)>1 else None), indent=2))
