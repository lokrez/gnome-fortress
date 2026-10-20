"""Bounded seed-1 rupture, restoration and spring: physical changes, no rollback."""
import argparse
import json
from dataclasses import asdict
from pathlib import Path
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    w=TerrainWorld(1)
    rock=next((x,y) for y,row in enumerate(w.cells) for x,c in enumerate(row) if c.terrain=='rock' and
              any(w.cell(nx,ny).terrain in ('grass','forest','hazard') for nx,ny in w.neighbors(x,y)))
    w.step(9);w.request('rupture',2,2);w.step(21)
    earlier_deaths=[e.actor for e in w.events if e.kind=='death']
    w.request('rewild',2,2);w.request('wellspring',*rock)
    path=args.output/'restoration.g5.sqlite';save_game(w,path);loaded=load_game(path)
    w.step(80);loaded.step(80);assert w.state()==loaded.state();w.validate()
    assert all(not w.agents[i].alive for i in earlier_deaths)
    print(json.dumps(dict(seed=1,rock_criterion='first row-major rock adjacent to traversable terrain',
        final=w.summary(),earlier_deaths_retained=earlier_deaths,interventions=[asdict(p) for p in w.interventions],
        continuation_exact=True,digest=w.digest()),indent=2))


if __name__=='__main__':main()
