"""python -m gnome_fortress [--headless --ticks N]."""
import argparse
import json
from pathlib import Path
import sqlite3
import signal
import time

from .runtime import Statistics, checkpoint_notice

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
    parser.add_argument("--rate", type=float, help="target ticks/second; headless default is unlimited")
    parser.add_argument("--forever", action="store_true", help="headless run until SIGINT/SIGTERM")
    parser.add_argument("--paused", action="store_true", help="start observer paused")
    parser.add_argument("--stats-every", type=float, default=10, help="statistics interval in seconds; 0 disables")
    args = parser.parse_args()
    if args.ticks < 0 or args.checkpoint_every < 1 or (args.frames is not None and args.frames < 1):
        parser.error("ticks must be nonnegative; checkpoint interval and frames must be positive")
    if args.rate is not None and (not 0 < args.rate < float('inf')):
        parser.error("rate must be finite and positive")
    if not 0 <= args.stats_every < float('inf'):
        parser.error("stats interval must be finite and nonnegative")
    if args.forever and not args.headless:
        parser.error("--forever requires --headless")
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
            remaining = None if args.forever else args.ticks
            statistics = Statistics(args.stats_every)
            since_save = 0
            while (remaining is None or remaining > 0) and not interrupted:
                tick_start = time.monotonic()
                world.step()
                if remaining is not None: remaining -= 1
                since_save += 1
                if since_save >= args.checkpoint_every:
                    checkpoint_notice(save(world, args.db))
                    since_save = 0
                    tick_start = time.monotonic()
                statistics.update(world)
                if args.rate:
                    while not interrupted:
                        delay = 1/args.rate-(time.monotonic()-tick_start)
                        if delay <= 0: break
                        time.sleep(min(delay,0.1))
        else:
            from .viewer import run
            run(world, args.db, save, args.checkpoint_every, args.frames, lambda: interrupted,
                rate=args.rate,paused=args.paused,stats_every=args.stats_every)
    finally:
        try:
            save(world, args.db)
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    print(json.dumps({**world.summary(), "digest": world.digest(), "checkpoint": str(args.db)}, sort_keys=True))


if __name__ == "__main__":
    main()
