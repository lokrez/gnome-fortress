"""Formatting detached execution evidence, without model access or predictions."""
def changes(before, after):
    fields=('health','hunger','thirst','fatigue','age','children')
    return ', '.join(f'{k} {after[k]-before[k]:+d}' for k in fields if after[k]!=before[k]) or 'no changes to listed quantities'


def observation_lines(record, detailed=False):
    if record is None:
        return ['No decision recorded.',
                'Detailed observation begins when enabled. Earlier decisions were not recorded.',
                'One step advances the whole world; a selected gnome may receive no decision slot.']
    r=record;lines=[f"Tick {r['tick']} • #{r['identity']:05d}",r['status']]
    before,after=r['biology_before'],r['biology_after']
    if after is not None:lines.append('Biology: '+changes(before,after)+'.')
    d=r['decision']
    if d is None:
        lines.append('No new action was selected by this individual.')
        for event in r.get('biology_events',[]):
            if event['kind']=='death':lines.append(f"Objective death event {event['index']}: {event['detail'].get('cause','unavailable')} at tick {event['tick']}.")
        end=r.get('tick_end')
        if end and after and end!=after:lines.append('Additional changes after biology: '+changes(after,end)+'.')
        return lines
    if not d['complete']:
        lines+=['Detailed execution evidence unavailable or incomplete.',d.get('unavailable') or 'Observation error.']
        return lines
    b,a=d['before'],d['after']
    lines += [f"Action: {d['action']}",d['rule'],
              f"Before: health {b['health']}, hunger {b['hunger']}, thirst {b['thirst']}, fatigue {b['fatigue']}.",
              'Action changes: '+changes(b,a)+'.']
    m=d['movement']
    if m:
        if m['candidates']:
            lines += [f"Movement: {tuple(m['origin'])} -> {tuple(m['destination'])}.",
                      f"Best score {m['best']}; "+('tied; existing random tie-break.' if m['tied'] else 'unique best (existing choice call).')]
            lines += [f"({c['x']}, {c['y']}) {c['terrain']}: {c['score']:+d}  learned {c['learned_contribution']:+d}"+
                      (' <- selected' if [c['x'],c['y']]==m['destination'] else '') for c in m['candidates']]
        else:lines.append('No passable adjacent candidates were evaluated.')
    for learning in d['learning']:
        lines += [f"Experience: {learning['key']}, reward {learning['reward']:+d}.",
                  f"Association: {learning['previous']:+d} -> {learning['current']:+d} (actual update)."]
    for e in d['events']:
        detail=e['detail']
        if e['kind']=='hazard':lines.append(f"Recorded hazard injury: {detail['damage']} health lost.")
        elif e['kind']=='death':lines.append(f"Recorded death: {detail.get('cause','unavailable')} at tick {e['tick']}.")
        elif e['kind']=='reproduce':lines.append(f"Recorded reproduction: partner #{e['target']:05d}, child #{detail['child']:05d}.")
        elif e['kind']=='social':lines.append(f"Recorded social encounter with #{e['target']:05d}; reward {detail['reward']}.")
    if detailed:
        lines+=['EXECUTED CONDITIONS (short-circuit checks)']
        lines += [('Branch entered: ' if check['entered'] else 'Branch not entered: ')+check['source'] for check in d['checks']]
        lines += ['Not every part of a short-circuit condition was necessarily evaluated.']
        lines += [f"Actual draw: {p['role']}, range {p['bound']}, value {p['sample']}" for p in d['random_attempts']]
        if d['random_attempt_count']>len(d['random_attempts']):lines.append('Additional random attempts omitted from this bounded display.')
        lines += [f"Peer #{p['identity']:05d} action changes: "+changes(p['before'],p['after'])+'.' for p in d['peers'] if p['before']!=p['after']]
        lines += [f"Relationship with #{p['identity']:05d}: outgoing {p['outgoing_before']} -> {p['outgoing_after']}, incoming {p['incoming_before']} -> {p['incoming_after']}" for p in d['peers'] if p['outgoing_before']!=p['outgoing_after'] or p['incoming_before']!=p['incoming_after']]
        lines += [f"Objective event index {e['index']}: {e['kind']} at tick {e['tick']}" for e in d['events']]
        lines+=['Candidate totals and learned contribution are shown; other score components are not separately recorded.']
    lines+=['Player observation differs from gnome memory. No motives or survival benefit are established.']
    return lines
