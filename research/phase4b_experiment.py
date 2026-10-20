"""Three-agent telephone harness: explicit scheduled interventions, no new biology."""
import argparse
import csv
import json
from pathlib import Path
import time

from gnome_fortress.telephone import TelephoneConfig, TelephoneWorld, save_telephone, load_telephone

CONDITIONS = ('individual', 'direct', 'multihop', 'masked', 'irrelevant')
CONFIG = {c: c if c != 'irrelevant' else 'multihop' for c in CONDITIONS}


class ThreeGnomesWorld(TelephoneWorld):
    implementation = 'phase4b-three-gnomes-v1'

    def __init__(self, seed=1, condition='multihop'):
        if condition not in CONDITIONS:
            raise ValueError('Unknown harness condition')
        super().__init__(seed, TelephoneConfig(CONFIG[condition]))
        self.protocol = dict(condition=condition, ticks=3, scripted_meetings=True)
        for a in list(self.living())[3:]:
            self.kill(a, 'experiment_setup')
        for row in self.cells:
            for cell in row:
                cell.terrain, cell.food = 'rock', 0
        for x,y,terrain in ((1,1,'grass'),(6,3,'grass'),(5,3,'hazard'),(4,3,'grass'),
                            (3,3,'grass'),(2,3,'grass'),(1,3,'grass'),(2,2,'hazard')):
            self.cells[y][x].terrain = terrain
        for a in self.agents.values():
            a.x = a.y = 1
        a,b,c = [self.agents[i] for i in (1,2,3)]
        for gnome in (a,b,c):
            gnome.hunger = gnome.thirst = gnome.fatigue = 0
            gnome.cooldown = 1000
            gnome.traits['curiosity'] = gnome.traits['caution'] = gnome.traits['sociability'] = 0
        a.x,a.y = 6,3; b.x,b.y = 4,3; c.x,c.y = 2,3
        b.hunger = 50  # disables peer-attraction scoring, not movement or contact
        b.traits['caution'] = 100  # same safe transit even without a warning
        c.sleep_until = 2
        self.move(a)  # real hazard consequence, not an invented learned value
        self.validate()

    def _content(self, sender, proof):
        key, value, intervention = super()._content(sender, proof)
        if self.protocol['condition'] == 'irrelevant' and len(proof['path']) > 1:
            return 'move:grass', value, 'irrelevant-key'
        return key, value, intervention

    def decide(self, agent):
        if self.tick > 3:
            return super().decide(agent)
        self.decision_count += 1
        if (self.tick, agent.id) == (1,1):
            self.contact(agent, self.agents[2]); agent.action = 'protocol_contact'
        elif (self.tick, agent.id) == (1,2):
            self.move(agent)
        elif (self.tick, agent.id) == (2,2):
            self.contact(agent, self.agents[3]); agent.action = 'protocol_contact'
        elif (self.tick, agent.id) == (3,3):
            self.move(agent)
        else:
            agent.action = 'protocol_wait'

    def validate(self):
        super().validate()
        if (not self.protocol or self.protocol['condition'] not in CONDITIONS
                or self.config.condition != CONFIG[self.protocol['condition']]):
            raise ValueError('Invalid controlled protocol configuration')


def load_probe(path):
    return load_telephone(path, ThreeGnomesWorld)


def probe(seed, condition):
    world = ThreeGnomesWorld(seed, condition)
    world.step(2)
    before_c_rng = world.rng.getstate()
    before_c_firsthand = world.origins.get(3, {}).get('move:hazard', {}).get('firsthand_count',0)
    world.step()
    c = world.agents[3]
    proofs = world.latest_moves[3]['knowledge_before']
    proof = proofs.get('move:hazard')
    two_hop = any(len(p['path']) == 3 for p in proofs.values())
    meaningful = proof is not None and not proof['masked']
    row = dict(seed=seed, condition=condition, messages=world.messages,
               meaningful_messages=world.meaningful_messages, opportunities=world.opportunities,
               attempts=world.contact_attempts, decisions=world.decision_count,
               two_hop_receipts=int(two_hop),
               meaningful_two_hop=int(meaningful and len(proof['path'])==3),
               firsthand_c_before=before_c_firsthand,
               hazard_entry=int(world.cell(c.x,c.y).terrain=='hazard'),
               c_x=c.x,c_y=c.y, a_value=world.agents[1].learned['move:hazard'],
               b_value=world.agents[2].learned.get('move:hazard',0),
               c_hazard_value_before=world.latest_moves[3]['learned'].get('move:hazard',0),
               c_grass_value_before=world.latest_moves[3]['learned'].get('move:grass',0),
               digest=world.digest())
    world.validate()
    return row, world, before_c_rng


def comparison_state(world):
    # Telephone records/episodes differ by design; all consequential core fields remain.
    from gnome_fortress.engine import World
    data=World.state(world)
    for agent in data['agents']:
        agent['memories']=[m for m in agent['memories'] if m['action']!='hear']
    return data


def run(output):
    if output.exists():
        raise ValueError('Use a new output directory; earlier experiments are preserved')
    output.mkdir(parents=True)
    rows=[]; changes=[]; controls_exact=True; c_controls_exact=True; rng_before_exact=True
    for seed in range(1,65):
        worlds={}; rngs={}; group={}
        for condition in CONDITIONS:
            row,w,rng=probe(seed,condition)
            rows.append(row); worlds[condition]=w; rngs[condition]=rng; group[condition]=row
        rng_before_exact &= all(rngs[c]==rngs['individual'] for c in CONDITIONS)
        controls_exact &= comparison_state(worlds['individual'])==comparison_state(worlds['masked'])
        c_controls_exact &= all((comparison_state(worlds[c])['agents'][2] == comparison_state(worlds['individual'])['agents'][2] and
                                 worlds[c].rng.getstate() == worlds['individual'].rng.getstate())
                                for c in ('direct', 'masked'))
        if group['individual']['hazard_entry'] and not group['multihop']['hazard_entry']:
            changes.append(seed)
    with (output/'probes.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    totals={c:{k:sum(r[k] for r in rows if r['condition']==c) for k in (
        'messages','meaningful_messages','opportunities','attempts','decisions','two_hop_receipts',
        'meaningful_two_hop','firsthand_c_before','hazard_entry')} for c in CONDITIONS}
    result=dict(seeds=64,ticks=3,totals=totals,changed_movement_seeds=changes,
                rng_identical_before_c_choice=rng_before_exact, individual_masked_core_exact=controls_exact, c_control_state_and_rng_exact=c_controls_exact)
    (output/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    # Seed 1 is published whether or not its individual counterfactual enters hazard.
    for condition in CONDITIONS:
        _,w,_=probe(1,condition)
        save_telephone(w,output/f'demo-{condition}.sqlite')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    run(parser.parse_args().output)
