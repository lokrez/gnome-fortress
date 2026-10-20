"""Bounded full-state equivalence against the exact pre-G1 engine commit."""
import hashlib
import json
import subprocess
import types

from gnome_fortress.engine import World
from gnome_fortress.game import GameWorld

REFERENCE='52374aa37b3f6bf5abf83b884c628f1bce5fb822'


def main():
    source=subprocess.check_output(['git','show',REFERENCE+':gnome_fortress/engine.py'])
    module=types.ModuleType('gnome_fortress._g1_reference');module.__package__='gnome_fortress'
    exec(compile(source,'<pre-G1 engine>','exec'),module.__dict__)
    checks=[]
    for seed in (1,42):
        reference,standard,game=module.World(seed),World(seed),GameWorld(seed)
        for boundary in (0,20,100,300):
            for w in (reference,standard,game):w.step(boundary-w.tick)
            assert reference.state()==standard.state()==World.state(game)
            assert reference.rng.getstate()==standard.rng.getstate()==game.rng.getstate()
            checks.append(dict(seed=seed,tick=boundary,digest=reference.digest(),exact=True))
    print(json.dumps(dict(reference=REFERENCE,source_sha256=hashlib.sha256(source).hexdigest(),
                          checks=checks),indent=2))


if __name__=='__main__':main()
