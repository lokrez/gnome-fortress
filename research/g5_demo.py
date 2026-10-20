"""Deterministic bounded Rupture demonstration, no forced gnome outcomes."""
import argparse
import json
from pathlib import Path
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.terrain_storage import save_game,load_game


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    a=TerrainWorld(1);a.step(9);before=a.summary()
    request=a.request('rupture',2,2)
    save_game(a,args.output/'rupture.g5.sqlite');b=load_game(args.output/'rupture.g5.sqlite')
    a.step(101);b.step(101);a.validate();assert a.state()==b.state()
    report=dict(seed=1,requested_tick=9,activation_tick=10,target=[2,2],radius=2,
        before=before,after=a.summary(),changes=request.changes,food_removed=request.food_removed,
        continuation_exact=True,digest=a.digest(),limitations='Observed outcomes, not individual causal attribution')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
