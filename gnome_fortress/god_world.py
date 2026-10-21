"""Opt-in terrain prototype. Run: python -m gnome_fortress.god_world"""
import argparse
import json
from pathlib import Path
import signal
import sqlite3

from .game_session import game_session,SaveInUse
from .terrain_game import TerrainWorld as GameWorld
from .terrain_storage import game_path,load_game,save_game,create_game,import_legacy

DEFAULT_SAVE=Path(__file__).resolve().parents[1]/'run-results/god-terrain/world.g5.sqlite'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--db',type=Path,default=DEFAULT_SAVE)
    p.add_argument('--import-legacy',type=Path,help='Copy a legacy world to an unused --db destination; never in-place')
    p.add_argument('--new',action='store_true',help='New world, requires an unused save path')
    p.add_argument('--paused',action='store_true')
    p.add_argument('--rate',type=float,default=15)
    p.add_argument('--checkpoint-every',type=int,default=300)
    p.add_argument('--frames',type=int,help='Bounded visual smoke run')
    p.add_argument('--capture',type=Path,help='Capture the actual final Pygame surface')
    p.add_argument('--headless',action='store_true')
    p.add_argument('--ticks',type=int,default=100)
    args=p.parse_args()
    if not 0<args.rate<float('inf') or args.checkpoint_every<1 or args.ticks<0 or (args.frames is not None and args.frames<1):
        p.error('Rate/interval/frames must be positive, ticks nonnegative')
    try:
        path=game_path(args.db)
        with game_session(path):
            _launch(args,p,path)
    except SaveInUse as error:
        p.error(f'Cannot open gameplay session: {error}')
    except (OSError,ValueError) as error:
        p.error(f'Gameplay session failed: {error}')


def _launch(args,p,path):
    try:
        path=game_path(args.db)
        if args.new and path.exists():p.error('--new needs an unused save path; preserved runs are not replaced')
        if args.import_legacy:
            if args.new:p.error('--new and --import-legacy are mutually exclusive')
            world=import_legacy(args.import_legacy,path)
        elif path.exists():world=load_game(path)
        else:
            world=GameWorld(args.seed);create_game(world,path)
    except (ValueError,OSError,sqlite3.Error,KeyError,TypeError,AssertionError) as error:
        p.error(f'Cannot open gameplay checkpoint: {error}')
    stopped=False
    def stop(signum,frame):
        nonlocal stopped
        stopped=True
    previous={sig:signal.signal(sig,stop) for sig in (signal.SIGINT,signal.SIGTERM)}
    try:
        if args.headless:
            for _ in range(args.ticks):
                if stopped or world.extinct:break
                world.step()
                if world.tick%args.checkpoint_every==0:save_game(world,path)
        else:
            from .terrain_viewer import run
            run(world,path,save_game,args.checkpoint_every,args.frames,lambda:stopped,
                args.rate,args.paused,args.capture)
    finally:
        try:save_game(world,path)
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
    print(json.dumps({**world.summary(),'extinct':world.extinct,'interventions':len(world.interventions),
                      'digest':world.digest(),'checkpoint':str(path)},sort_keys=True))


if __name__=='__main__':main()
