"""Runnable A -> B -> C demonstration and all five matched content controls."""
import argparse
import json
from pathlib import Path

from gnome_fortress.telephone import save_telephone
from research.phase4b_experiment import CONDITIONS, probe
from research.phase4b_inspect import inspect_agent


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed',type=int,default=1)
    parser.add_argument('--checkpoint',type=Path,help='Optional NEW multihop checkpoint path')
    args=parser.parse_args()
    if args.checkpoint and args.checkpoint.exists():parser.error('Checkpoint exists; use a new path')
    result=dict(seed=args.seed, protocol='Controlled meetings and waits in eight scheduled decisions over three ticks; 57 founders killed for setup',conditions={})
    for condition in CONDITIONS:
        row,w,_=probe(args.seed,condition)
        result['conditions'][condition]=dict(measurements=row,c_evidence=inspect_agent(w,3))
        if args.checkpoint and condition=='multihop':save_telephone(w,args.checkpoint)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
