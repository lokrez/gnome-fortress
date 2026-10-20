"""Run an isolated warning-versus-preference movement demonstration."""
import argparse
import json

from research.phase4c_matrix import MatrixWorld, MODES, DEPTHS, MARGINS, STRENGTHS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=1)
    p.add_argument('--source',type=int,choices=STRENGTHS,default=-64)
    p.add_argument('--depth',type=int,choices=DEPTHS,default=2)
    p.add_argument('--margin',type=int,choices=MARGINS,default=1)
    p.add_argument('--rounding',choices=MODES,default='floor')
    p.add_argument('--json',action='store_true',help='Include complete machine-readable rows')
    args=p.parse_args();w=MatrixWorld(args.seed,args.depth)
    rows=[w.case(args.source,args.margin,args.rounding,c) for c in ('individual','multihop','ablation')]
    print('Research-only synthetic source readout; real source experience is recorded separately.')
    print('These contacts are prescribed local opportunities, not autonomous meetings.')
    print(f'Seed {args.seed}; depth {args.depth}; source {args.source}; margin {args.margin}; arithmetic {args.rounding}')
    print(f'Actual source experience score: {w.actual_source_value}')
    for row in rows:
        print(f"{row['condition']:12} received={row['acquired_hazard']:3} choice=({row['chosen_x']},{row['chosen_y']}) {row['chosen_terrain']:6} changed={row['decision_changed']} firsthand_before={row['firsthand_before']}")
        print('  candidates before:',row['before'],'after:',row['after'])
        if row['condition']=='multihop':print('  receipts:',json.dumps(row['receipts'],sort_keys=True))
    if args.json:print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
