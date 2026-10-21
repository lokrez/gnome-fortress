"""Disposable, selected-identity execution evidence. Never part of a World graph.

The decision algorithm is not copied here. A thread-local Python execution trace
reads its actual locals while that ONE decision executes. No caller callbacks,
extra random draws, changed action rules, or persistent events are introduced.
"""
import ast
from collections import deque
import copy
import inspect
import sys
import textwrap
from weakref import WeakKeyDictionary

_OBSERVERS = WeakKeyDictionary()
_FIELDS = ('x','y','age','health','hunger','thirst','fatigue','sleep_until',
           'alive','died','death_cause','cooldown','children','action')
RULES = {
    'drink': 'Drinking rule: thirst >= 30 and accessible water.',
    'eat': 'Eating rule: hunger >= 30 and local food >= 10.',
    'sleep': 'Sleeping rule: fatigue >= 65, hunger < 80, thirst < 75.',
    'reproduce': 'Reproduction rule: eligible parents and a successful existing probability check.',
    'socialize': 'Social rule: nearby peers, qualifying needs and a successful existing probability check.',
    'move': 'Movement fallback: higher-priority actions were not selected.',
    'wait': 'Movement fallback: no legal adjacent destination.',
}


def for_world(world):
    return _OBSERVERS.get(world)


def values(agent):
    return {k: getattr(agent, k) for k in _FIELDS}


class DecisionObservation:
    """One session, one identity, 128 recent complete-tick records by default.

    Selecting another identity starts a new session. Stop preserves its buffer;
    death stops new records. Records are detached values, not model references.
    """
    def __init__(self, capacity=128):
        if type(capacity) is not int or not 1 <= capacity <= 128:
            raise ValueError('Observation capacity must be between 1 and 128')
        self.records = deque(maxlen=capacity)
        self.identity = None
        self.enabled = False
        self.error = None
        self.started_tick = None
        self.pending = None
        self._branches = None
        self._draw_roles = {}

    def start(self, world, identity):
        agent = world.agents.get(identity)
        if agent is None or not agent.alive:
            return False
        if self.identity != identity:
            self.records.clear()
        self.identity = identity
        self.started_tick = world.tick
        self.enabled = True
        self.error = None
        try:
            # Derive source locations, never a second copy of the decision rules.
            from .engine import World
            source, first = inspect.getsourcelines(World.decide)
            tree = ast.parse(textwrap.dedent(''.join(source)))
            self._branches = [(first+n.lineno-1, first+n.body[0].lineno-1,
                               ast.get_source_segment(textwrap.dedent(''.join(source)), n.test))
                              for n in ast.walk(tree) if isinstance(n, ast.If)]
            for n in ast.walk(tree):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr=='randrange':
                    argument=ast.unparse(n.args[0])
                    self._draw_roles[first+n.lineno-1] = ('reproduction probability' if argument=='1000' else
                        'social probability' if argument=='100' else 'social partner selection')
            _OBSERVERS[world] = self
        except Exception as exc:
            self.stop(world)
            self.error = f'Execution source unavailable: {type(exc).__name__}'
            return False
        return True

    def stop(self, world):
        if _OBSERVERS.get(world) is self:
            del _OBSERVERS[world]
        self.enabled = False
        self.pending = None

    def begin(self, world):
        try:
            a = world.agents.get(self.identity)
            if not self.enabled or a is None or not a.alive:
                self.stop(world)
                return
            self._biology_event_start = len(world.events)
            self.pending = dict(tick=world.tick, identity=a.id, scheduled=False,
                                biology_before=values(a), biology_after=None,
                                decision=None, status=None, biology_events=[])
        except Exception as exc:
            self.error = f'Observation unavailable: {type(exc).__name__}'
            self.pending = None

    def after_biology(self, world):
        try:
            if self.pending is not None:
                self.pending["biology_after"] = values(world.agents[self.identity])
                self.pending['biology_events'] = [dict(index=i,tick=e.tick,kind=e.kind,
                    actor=e.actor,target=e.target,detail=copy.deepcopy(e.detail))
                    for i,e in enumerate(world.events[self._biology_event_start:],self._biology_event_start)
                    if e.actor==self.identity or e.target==self.identity]
        except Exception as exc:
            self.error = f"Biology observation unavailable: {type(exc).__name__}"

    def invoke(self, world, agent, function):
        """Call the real decision exactly once, even if observation fails.

        An existing debugger/coverage tracer is left in control. In that case we
        record an explicit unavailable explanation, not reconstructed evidence.
        """
        record = self.pending
        if record is None or agent.id != self.identity:
            return function(agent)
        try:
            record['scheduled'] = True
            decision = dict(before=values(agent), after=None, action=None,
                            rule=None, checks=[], random_attempts=[], random_attempt_count=0, movement=None,
                            learning=[], peers=[], events=[], complete=False,
                            nearby_count=0, context=dict(terrain=world.cell(agent.x,agent.y).terrain,
                                         food=world.cell(agent.x,agent.y).food))
            record['decision'] = decision
            event_start = len(world.events)
            learned_before = dict(agent.learned)
            peer_before = {}
            executed_lines = set()
            remembering = {}
            from .engine import World
            codes = (World.decide.__code__, World.move.__code__, World.remember.__code__,
                     World._nearby_agents.__code__)
            old_trace = sys.gettrace()
        except Exception as exc:
            self.error = f'Observation setup failed: {type(exc).__name__}'
            return function(agent)

        def trace(frame, event, arg):
            try:
                code = frame.f_code
                if code not in codes and code.co_name != 'randrange':
                    return None
                if code is World.decide.__code__ and event == 'line':
                    executed_lines.add(frame.f_lineno)
                    return trace
                if event == 'call' and code is not World.decide.__code__:
                    frame.f_trace_lines = False
                local = frame.f_locals
                if code is World.remember.__code__ and local.get('a') is agent:
                    if event == 'call':
                        key = f"{local['action']}:{local['feature']}"
                        remembering[id(frame)] = (key, agent.learned.get(key,0))
                    elif event == 'return':
                        key, previous = remembering.pop(id(frame))
                        decision['learning'].append(dict(key=key, previous=previous,
                            current=agent.learned[key], reward=local['reward'],
                            action=local['action'], feature=local['feature'],
                            position=[agent.x,agent.y]))
                elif code is World._nearby_agents.__code__ and event == 'return' and local.get('a') is agent:
                    decision['nearby_count'] = len(arg)
                    for peer in arg[:64]:
                        if peer.id not in peer_before:
                            peer_before[peer.id] = dict(state=values(peer),
                                outgoing=agent.relationships.get(peer.id,0),
                                incoming=peer.relationships.get(agent.id,0))
                elif code is World.move.__code__ and event == 'return' and local.get('a') is agent:
                    candidates = [dict(score=s, x=x, y=y,
                        terrain=world.cell(x,y).terrain,
                        learned_contribution=learned_before.get(f'move:{world.cell(x,y).terrain}',0))
                        for s,x,y in local['candidates']]
                    best = local.get('best')
                    decision['movement'] = dict(origin=[decision['before']['x'],decision['before']['y']],
                        candidates=candidates, best=best,
                        tied=sum(c['score']==best for c in candidates)>1,
                        choice_called=bool(candidates),
                        destination=[agent.x,agent.y] if candidates else None,
                        observed_food=[list(p) for p in local['food']],
                        observed_water=[list(p) for p in local['water']],
                        observed_peers=[list(p) for p in local['peers'][:64]],
                        observed_peer_count=len(local['peers']))
                elif code.co_name == 'randrange' and event == 'return':
                    caller = frame.f_back
                    if caller and caller.f_code is World.decide.__code__:
                        stop = local.get('stop')
                        limit = local.get('start') if stop is None else stop
                        partner = caller.f_locals.get('b')
                        role = self._draw_roles.get(caller.f_lineno,'Observed decision randrange')
                        decision['random_attempt_count'] += 1
                        if len(decision['random_attempts']) >= 64:
                            return trace
                        decision['random_attempts'].append(dict(line=caller.f_lineno,
                            bound=limit, sample=arg,
                            role=role,
                            partner=partner.id if role=='reproduction probability' and partner is not None else None))
            except Exception as exc:
                self.error = f'Incomplete execution evidence: {type(exc).__name__}'
            # Only instrument known decision helpers and actual random calls.
            if frame.f_code in codes or frame.f_code.co_name == 'randrange':
                return trace
            return None

        installed = False
        if old_trace is not None:
            self.error = 'Detailed evidence unavailable while another Python tracer is active.'
        else:
            try:
                sys.settrace(trace)
                installed = True
            except Exception as exc:
                self.error = f'Execution tracing unavailable: {type(exc).__name__}'
        succeeded = False
        try:
            result = function(agent)
            succeeded = True
            return result
        finally:
            if installed:
                sys.settrace(None)
            try:
                decision['after'] = values(agent)
                movement = decision['movement']
                action = ('move' if movement['candidates'] else 'wait') if movement is not None else agent.action
                decision['action'] = action if installed else None
                decision['rule'] = RULES.get(action, 'Rule not recorded.') if installed else 'Rule not recorded.'
                decision['checks'] = [dict(source=condition, entered=body in executed_lines)
                                      for line,body,condition in self._branches if line in executed_lines]
                decision['events'] = [dict(index=i,tick=e.tick,kind=e.kind,actor=e.actor,
                                           target=e.target,detail=copy.deepcopy(e.detail))
                                      for i,e in enumerate(world.events[event_start:],event_start)]
                decision['peers'] = [dict(identity=i,before=before['state'],after=values(world.agents[i]),
                                         outgoing_before=before['outgoing'],outgoing_after=agent.relationships.get(i,0),
                                         incoming_before=before['incoming'],incoming_after=world.agents[i].relationships.get(agent.id,0))
                                     for i,before in peer_before.items()]
                decision['complete'] = self.error is None and succeeded
                decision['unavailable'] = self.error or (None if succeeded else 'Engine decision did not complete.')
            except Exception as exc:
                self.error = f'Incomplete decision outcome: {type(exc).__name__}'

    def finish(self, world):
        try:
            record = self.pending
            if record is None:
                return
            a = world.agents.get(self.identity)
            if a is None:
                record['status'] = 'Individual record unavailable.'
            else:
                if record['biology_after'] is None:
                    # No decision: no selected action can be attributed to this tick.
                    record['biology_after'] = values(a)
                record['tick_end'] = values(a)
                record['status'] = ('Decision recorded.' if record['scheduled'] else
                    f'No decision slot: died during biology ({a.death_cause}).' if not a.alive else
                    'No decision slot: sleeping.' if a.sleep_until>world.tick else
                    'No decision slot: eligible but not assigned.')
            self.records.append(record)
            self.pending = None
            if a is None or not a.alive:
                self.stop(world)
        except Exception as exc:
            self.error = f'Incomplete tick observation: {type(exc).__name__}'
            self.pending = None
