"""Research-only observation of the original movement function; no copied scorer."""
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
import random
import sys

from gnome_fortress.engine import World

KEY='move:hazard'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


class MixedOrigin(ValueError):
    pass


def pure_social(world, agent):
    origin=world.origins.get(agent.id,{}).get(KEY,{})
    social=origin.get('social_count',0)>0
    firsthand=origin.get('firsthand_count',0)>0
    if social and firsthand:
        raise MixedOrigin('EMA mixes social and firsthand information; no clean decomposition')
    return social and not firsthand


class ReadoutMask(dict):
    """Suppress only the movement lookup, never stored values or learning updates."""
    def get(self,key,default=None):
        if key==KEY and sys._getframe(1).f_code is World.move.__code__:
            return 0
        return super().get(key,default)


@contextmanager
def masked_readout(world, agent, enabled=True):
    apply=enabled and pure_social(world,agent)
    if apply:agent.learned=ReadoutMask(agent.learned)
    try:yield apply
    finally:
        if apply:agent.learned=dict(agent.learned)


class _ScoresCaptured(Exception):
    pass


class _ScoreTrap:
    def choice(self, choices):
        frame=sys._getframe(1)
        if frame.f_code is not World.move.__code__:
            raise RuntimeError('Unexpected scoring call site')
        raise _ScoresCaptured(list(frame.f_locals['candidates']))


def scores(world,agent,ablate=False):
    """Stop the actual scorer before choice/side effects. Consume no random draw."""
    original_rng=world.rng;action=agent.action
    try:
        with masked_readout(world,agent,ablate):
            world.rng=_ScoreTrap()
            try:World.move(world,agent)
            except _ScoresCaptured as captured:return captured.args[0]
            return []
    finally:
        world.rng=original_rng;agent.action=action


def best(candidates):
    if not candidates:return []
    value=max(s for s,_,_ in candidates)
    return [c for c in candidates if c[0]==value]


def coupled_choice(candidates,rng_state):
    options=best(candidates)
    if not options:return None
    clone=random.Random(0);clone.setstate(rng_state)
    return clone.choice(options)


class ChoiceObserver:
    def __init__(self,base,callback):self.base,self.callback=base,callback
    def __getattr__(self,name):return getattr(self.base,name)
    def choice(self,choices):
        frame=sys._getframe(1)
        if frame.f_code is World.move.__code__:
            return self.callback(frame.f_locals['a'],list(frame.f_locals['candidates']),choices,self.base)
        return self.base.choice(choices)


def execute(world,agent,operation,ablate=False,full_boundary=False):
    records=[];original=world.rng
    def callback(actor,candidates,options,rng):
        if actor.id!=agent.id:return rng.choice(options)
        raw=asdict(actor)
        unrelated={k:v for k,v in raw.items() if k not in ('learned','memories')}
        row=dict(scores=candidates,rng_before=digest(rng.getstate()),
                 actor_before=digest(raw),unrelated_before=digest(unrelated),
                 stored_hazard=actor.learned.get(KEY,0),
                 firsthand_before=world.origins.get(actor.id,{}).get(KEY,{}).get('firsthand_count',0))
        if full_boundary:row['full_boundary']=digest(world.state())
        chosen=rng.choice(options)
        row['chosen']=chosen;records.append(row)
        return chosen
    try:
        with masked_readout(world,agent,ablate) as applied:
            world.rng=ChoiceObserver(original,callback)
            operation()
    finally:world.rng=original
    if len(records)!=1:raise ValueError('Expected exactly one scored movement decision')
    result=records[0];result['readout_masked']=applied
    result['terrain']=world.cell(agent.x,agent.y).terrain
    result['rng_after']=digest(original.getstate())
    return result
