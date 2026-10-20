"""Bounded verification and analysis of already completed Phase 4A pilot."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import random
import statistics

from gnome_fortress.communication import (CommunicationConfig, CommunicationWorld,
                                          load_experiment)
from gnome_fortress.engine import World
from gnome_fortress.observatory import Observation
from research.phase4a_experiment import behavioral_state


def state_without_episode_records(world):
    data = behavioral_state(world)
    for a in data['agents']:
        a['memories'] = []
    return data


def paired_interval(differences, seed=404):
    rng = random.Random(seed)  # analysis-only RNG; never passed to a world
    means = sorted(statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(10000))
    return dict(mean=statistics.mean(differences), bootstrap_percentile_95=[means[249], means[9749]],
                differences=differences)


def verify(directory):
    rows = list(csv.DictReader((directory / 'pilot.csv').open()))
    by_seed = {}
    manifest = []
    replay = []
    example = None
    for row in rows:
        seed = int(row['seed']); condition = row['condition']
        path = directory / f'pilot-{seed:02d}-{condition}.sqlite'
        loaded = load_experiment(path)
        assert loaded.digest() == row['digest']
        fresh = CommunicationWorld(seed, CommunicationConfig(condition)); fresh.step(int(row['tick']))
        assert fresh.state() == loaded.state()
        assert fresh.digest() == row['digest']
        by_seed.setdefault(seed, {})[condition] = loaded
        # Verify exact continuation, including histories/provenance/RNG.
        restored = CommunicationWorld.from_state(loaded.state())
        restored.step(10)
        continuation = CommunicationWorld.from_state(fresh.state()); continuation.step(10)
        assert restored.state() == continuation.state()
        replay.append(dict(seed=seed, condition=condition, digest=row['digest'], replay_exact=True,
                           continuation_ticks=10, continuation_exact=True))
        if example is None and condition == 'social':
            candidates = [a for a in loaded.living() if a.parents and loaded.origins.get(a.id, {}).get('move:hazard', {}).get('social_count',0)]
            if candidates:
                a = min(candidates, key=lambda a:a.id)
                view = Observation(loaded, live=False); view.select_population('descendants')
                view.selected = view.roster.index(a.id)
                (directory.parent / 'descendant-persona.txt').write_text('\n'.join(view.persona())+'\n')
                view.offset = 20
                (directory.parent / 'descendant-screen.txt').write_text('\n'.join(view.layout(140,35))+'\n')
                example = dict(seed=seed, id=a.id, parents=a.parents,
                               origin=loaded.origins[a.id]['move:hazard'])
    for seed, worlds in by_seed.items():
        reference = World(seed); reference.step(worlds['individual'].tick)
        assert World.state(worlds['individual']) == reference.state()
        assert state_without_episode_records(worlds['individual']) == state_without_episode_records(worlds['sham'])
        assert worlds['individual'].origins == worlds['sham'].origins
    for path in sorted(directory.glob('*.sqlite')):
        with path.open('rb') as file:
            digest = hashlib.file_digest(file, 'sha256').hexdigest()
        manifest.append(dict(path=path.name, bytes=path.stat().st_size, sha256=digest))
    result = dict(exact_replays=replay, reference_exact_seeds=sorted(by_seed),
                  sham_behavior_and_rng_exact_seeds=sorted(by_seed), descendant_example=example)
    result['comparisons'] = {}
    for metric in ('living','births','deaths','hazards'):
        differences = []
        for seed in sorted(by_seed):
            group = {r['condition']:r for r in rows if int(r['seed'])==seed}
            differences.append(int(group['social'][metric])-int(group['individual'][metric]))
        result['comparisons'][metric] = paired_interval(differences)
    result['totals'] = {condition:{metric:sum(float(r[metric]) for r in rows if r['condition']==condition)
                                  for metric in ('births','deaths','hazards','messages','opportunities','decisions','seconds','hook_seconds')}
                        for condition in ('individual','social','sham')}
    (directory.parent / 'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    (directory.parent / 'checkpoint-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='exact_replays'},indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    verify(parser.parse_args().directory)
