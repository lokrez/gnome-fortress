"""Read-only companion inspector for Phase 4B controlled checkpoint provenance."""
import argparse
import copy
import json
from pathlib import Path

from gnome_fortress.observatory import load_snapshot
from research.phase4b_experiment import load_probe


def inspect_agent(world, identity):
    agent=world.agents[identity]
    move=copy.deepcopy(world.latest_moves.get(identity))
    proofs=copy.deepcopy(world.proofs.get(identity,{}))
    used=move.get('knowledge_before',{}) if move else {}
    return dict(agent=identity, tick=world.tick, alive=agent.alive,
                condition=world.protocol['condition'], current_associations=dict(agent.learned),
                current_proofs=proofs, knowledge_before_latest_movement=used,
                acquisition_evidence={key:dict(root_source=p['root']['agent'],
                    received_from=p['receipts'][-1]['sender'] if p['receipts'] else None,
                    source_path=p['path'], forwarded=len(p['path'])>2,
                    firsthand_at_acquisition=p['receipts'][-1]['firsthand_before'] if p['receipts'] else 'direct',
                    masked=p['masked'], receipts=p['receipts']) for key,p in used.items()},
                recorded_movement=move,
                bounded_audit_entries=len(world.audit),
                note='Association strengths are not certainty probabilities; historical paths do not imply independent witnesses.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkpoint',type=Path)
    parser.add_argument('--agent',type=int,default=3)
    args=parser.parse_args()
    world=load_snapshot(args.checkpoint,loader=load_probe)
    if args.agent not in world.agents:parser.error('Unknown agent ID')
    print(json.dumps(inspect_agent(world,args.agent),indent=2))


if __name__=='__main__':main()
