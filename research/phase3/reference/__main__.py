"""python -m gnome_fortress [--headless --ticks N]."""
import argparse
import json
from pathlib import Path
import sqlite3
import signal

from .engine import World
from .storage import load, save


def main():
    parser = argparse.ArgumentParser(description="Gnome Fortress: deterministic artificial life")
    parser.add_argument("--seed", type=int, default=1, help="seed for a new world (default 1)")
    parser.add_argument("--db", type=Path, default=Path("fortress.sqlite"), help="SQLite checkpoint")
    parser.add_argument("--new", action="store_true", help="explicitly replace checkpoint with a new world")
    parser.add_argument("--headless", action="store_true", help="run without Pygame")
    parser.add_argument("--ticks", type=int, default=1000, help="additional ticks in headless mode")
    parser.add_argument("--checkpoint-every", type=int, default=300)
    parser.add_argument("--frames", type=int, help="close viewer after N frames (smoke check)")
    args = parser.parse_args()
    if args.ticks < 0 or args.checkpoint_every < 1 or (args.frames is not None and args.frames < 1):
        parser.error("ticks must be nonnegative; checkpoint interval and frames must be positive")
    try:
        world = load(args.db) if args.db.exists() and not args.new else World(args.seed)
    except (sqlite3.Error, ValueError, KeyError, AssertionError) as error:
        parser.error(f"Cannot load checkpoint: {error}")
    interrupted = False

    def request_stop(signum, frame):
        nonlocal interrupted
        interrupted = True  # Defer shutdown until a complete simulation tick.

    previous = {sig: signal.signal(sig, request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    try:
        if args.headless:
            remaining = args.ticks
            since_save = 0
            while remaining and not interrupted:
                world.step()
                remaining -= 1
                since_save += 1
                if since_save >= args.checkpoint_every:
                    save(world, args.db)
                    since_save = 0
        else:
            from .viewer import run
            run(world, args.db, save, args.checkpoint_every, args.frames, lambda: interrupted)
    finally:
        try:
            save(world, args.db)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    print(json.dumps({**world.summary(), "digest": world.digest(), "checkpoint": str(args.db)}, sort_keys=True))


if __name__ == "__main__":
    main()
