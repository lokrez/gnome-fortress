"""Fast two-gnome demonstration, with all three conditions and explicit evidence."""
import argparse
import json

from research.phase4a_experiment import probe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=1)
    args = parser.parse_args()
    result = dict(seed=args.seed,
                  intervention='58 founders killed for setup; two active gnomes in controlled arena; sender physically encounters hazard at tick 0; one scheduled tick follows',
                  conditions={})
    for condition in ('individual', 'social', 'sham'):
        row, world = probe(args.seed, condition)
        result['conditions'][condition] = dict(
            outcome=row,
            source_firsthand_episode=next(vars(m) for m in world.agents[1].memories if m.action=='move' and m.feature=='hazard'),
            recipient_episodes=[vars(m) for m in world.agents[2].memories],
            recipient_origin=world.origins.get(2, {}).get('move:hazard'),
            message_events=[vars(e) for e in world.events if e.kind=='communication'])
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
