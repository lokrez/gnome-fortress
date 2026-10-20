"""Reproducible small Phase 4A probes/pilot; no endurance campaign."""
import argparse
import csv
import json
from pathlib import Path
import time

from gnome_fortress.communication import (CONDITIONS, CommunicationConfig,
                                          CommunicationWorld, save_experiment)
from gnome_fortress.engine import World


def two_gnomes(seed, condition):
    """Explicit arena intervention, not a claim about spontaneous population life."""
    world = CommunicationWorld(seed, CommunicationConfig(condition))
    for agent in list(world.living())[2:]:
        world.kill(agent, 'experiment_setup')
    for row in world.cells:
        for cell in row:
            cell.terrain, cell.food = 'rock', 0
    for x, y, terrain in ((1, 1, 'grass'), (5, 3, 'grass'), (4, 3, 'hazard'),
                           (3, 3, 'grass'), (3, 2, 'grass')):
        world.cells[y][x].terrain = terrain
    for agent in world.agents.values():
        agent.x = agent.y = 1
    sender, recipient = world.agents[1], world.agents[2]
    sender.x, sender.y = 5, 3
    recipient.x, recipient.y = 3, 3
    for agent in (sender, recipient):
        agent.hunger = agent.thirst = agent.fatigue = 0
        agent.cooldown = 1000  # isolate movement/communication from reproduction
        agent.traits['caution'] = agent.traits['curiosity'] = 0
    sender.traits['sociability'] = 100
    recipient.traits['sociability'] = 0
    # Exactly one traversable neighbor forces genuine physical hazard experience.
    # Uses the real movement, damage, Episode and association update implementations.
    world.move(sender)
    assert (sender.x, sender.y) == (4, 3)
    assert not recipient.memories and 'move:hazard' not in recipient.learned
    world.validate()
    return world


def behavioral_state(world):
    """Sham records are intentionally different; compare all consequential fields."""
    data = World.state(world)
    data['events'] = [e for e in data['events'] if e['kind'] != 'communication']
    for agent in data['agents']:
        agent['memories'] = [e for e in agent['memories'] if e['action'] != 'hear']
    return data


def probe(seed, condition):
    world = two_gnomes(seed, condition)
    source_value = world.agents[1].learned['move:hazard']
    world.step()
    recipient = world.agents[2]
    origin = world.origins.get(2, {}).get('move:hazard', {})
    row = dict(seed=seed, condition=condition, messages=world.messages,
               opportunities=world.opportunities, source_value=source_value,
               recipient_x=recipient.x, recipient_y=recipient.y,
               recipient_hazard=int(any(e.kind == 'hazard' and e.actor == 2 for e in world.events)),
               recipient_heard=origin.get('social_count', 0),
               recipient_firsthand=origin.get('firsthand_count', 0),
               recipient_value=recipient.learned.get('move:hazard', 0), digest=world.digest())
    return row, world


def summarize(world, elapsed):
    events = world.events
    return dict(tick=world.tick, living=len(world.living()),
                births=sum(e.kind == 'birth' and not e.detail.get('founder') for e in events),
                deaths=sum(e.kind == 'death' for e in events),
                hazards=sum(e.kind == 'hazard' for e in events),
                opportunities=world.opportunities, messages=world.messages,
                social_recipients=sum(records.get('move:hazard', {}).get('social_count', 0) > 0
                                      for records in world.origins.values()),
                decisions=world.decision_count, seconds=elapsed,
                ticks_per_second=world.tick/elapsed,
                hook_seconds=world.hook_seconds, slots=len(world.slots), digest=world.digest())


def csv_write(path, rows):
    with path.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def run(output, pilot_ticks=500, pilot_seeds=8):
    if output.exists():
        raise ValueError('Use a new output directory; preserving previous experimental results')
    output.mkdir(parents=True)
    probes, examples = [], []
    sham_exact = True
    for seed in range(1, 65):
        worlds = {}
        for condition in CONDITIONS:
            row, world = probe(seed, condition)
            probes.append(row); worlds[condition] = world
        sham_exact &= behavioral_state(worlds['individual']) == behavioral_state(worlds['sham'])
        if (worlds['social'].origins.get(2, {}).get('move:hazard', {}).get('social_count', 0)
                and worlds['individual'].agents[2].x == 4 and worlds['social'].agents[2].x == 3):
            examples.append(seed)
    csv_write(output / 'probes.csv', probes)
    if examples:
        seed = examples[0]
        for condition in CONDITIONS:
            world = two_gnomes(seed, condition); world.step()
            save_experiment(world, output / f'demo-{condition}.sqlite')
            (output / f'demo-{condition}.json').write_text(json.dumps(world.state(), indent=2)+'\n')
    population = []
    for seed in range(1, pilot_seeds + 1):
        for condition in CONDITIONS:
            world = CommunicationWorld(seed, CommunicationConfig(condition))
            start = time.perf_counter(); world.step(pilot_ticks); elapsed = time.perf_counter()-start
            world.validate()
            population.append(dict(seed=seed, condition=condition, **summarize(world, elapsed)))
            save_experiment(world, output / f'pilot-{seed:02d}-{condition}.sqlite')
    csv_write(output / 'pilot.csv', population)
    result = dict(probe_seeds=64, probe_ticks=1, pilot_seeds=pilot_seeds, pilot_ticks=pilot_ticks,
                  example_seed=examples[0] if examples else None, changed_movement_seeds=examples,
                  sham_behavior_exact=sham_exact,
                  hazards_by_condition={c:sum(r['recipient_hazard'] for r in probes if r['condition']==c) for c in CONDITIONS},
                  contact_seeds=sum(r['opportunities'] for r in probes if r['condition']=='individual'),
                  socially_informed_without_firsthand=sum(r['recipient_heard']>0 and r['recipient_firsthand']==0
                                                         for r in probes if r['condition']=='social'))
    (output / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pilot-ticks', type=int, default=500)
    parser.add_argument('--pilot-seeds', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.pilot_ticks <= 1000 or not 1 <= args.pilot_seeds <= 8:
        parser.error('This prototype runner is limited to 1–1000 ticks and 1–8 pilot seeds')
    run(args.output, args.pilot_ticks, args.pilot_seeds)


if __name__ == '__main__':
    main()
