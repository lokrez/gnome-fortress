"""Isolated synthetic transport/readout matrix. Verified modules are never edited."""
from dataclasses import asdict
import copy

from gnome_fortress.communication import CommunicationWorld, origin_record
from gnome_fortress.engine import World
from gnome_fortress.model import Episode
from research.phase4c_tools import best, coupled_choice, digest, execute, scores

STRENGTHS=(-64,-32,-16,-8,-4,-2,-1,0)
DEPTHS=(1,2,3,7)
MARGINS=(-8,-4,-2,-1,0,1,2,4,8,16,32,50)
MODES=('floor','truncate','symmetric')
CONDITIONS=('individual','direct','multihop','masked','irrelevant','ablation')
SEEDS=(1,2,3,4)


def divide(value,divisor,mode):
    if mode=='floor':return value//divisor
    sign=-1 if value<0 else 1
    if mode=='truncate':return sign*(abs(value)//divisor)
    if mode=='symmetric':return sign*((abs(value)+divisor//2)//divisor)
    raise ValueError('Unknown arithmetic')


def attenuate(value,mode,old=0):
    packet=divide(value,2,mode)
    return packet,max(-100,min(100,divide(3*old+packet,4,mode)))


class MatrixWorld(CommunicationWorld):
    def __init__(self,seed,depth):
        super().__init__(seed)
        self.depth=depth;self.target_id=depth+1
        for a in list(self.living())[depth+1:]:self.kill(a,'experiment_setup')
        for row in self.cells:
            for cell in row:cell.terrain,cell.food='rock',0
        cx=12-depth
        tiles=[(1,1,'grass'),(13,2,'grass'),(12,2,'hazard')]
        tiles += [(12-i,3,'grass') for i in range(depth+1)]
        tiles += [(cx,2,'hazard'),(cx,4,'grass'),(cx-1,3,'grass')]
        for x,y,t in tiles:self.cells[y][x].terrain=t
        for a in self.agents.values():a.x=a.y=1
        for index,a in enumerate(self.living()):
            a.x,a.y=12-index,3
            a.hunger=a.thirst=a.fatigue=0;a.cooldown=1000
            a.traits['curiosity']=a.traits['caution']=a.traits['sociability']=0
        source=self.agents[1];source.x,source.y=13,2
        World.move(self,source)
        assert (source.x,source.y)==(12,2)
        self.actual_source_value=source.learned['move:hazard']
        source.visits['13,2']=1
        World.move(self,source)
        assert (source.x,source.y)==(12,3)
        self.validate()
        self.template_digest=digest(World.state(self))
        self._base_agents={i:copy.deepcopy(self.agents[i].__dict__) for i in range(1,depth+2)}
        self._base_origins=copy.deepcopy(self.origins)
        self._base_events=len(self.events);self._base_rng=self.rng.getstate()

    def reset(self,source_value,margin):
        for identity,data in self._base_agents.items():
            self.agents[identity].__dict__.clear()
            self.agents[identity].__dict__.update(copy.deepcopy(data))
        self.origins=copy.deepcopy(self._base_origins)
        del self.events[self._base_events:];self.rng.setstate(self._base_rng)
        self.agents[1].learned['move:hazard']=source_value  # declared synthetic intervention
        c=self.agents[self.target_id]
        if margin<=0:visits=0;caution=-margin*5
        elif margin<=8:visits=1;caution=(8-margin)*5
        else:visits={16:2,32:4,50:7}[margin];caution=0
        c.traits['caution']=caution
        c.visits={f'{x},{y}':visits for x,y in self.neighbors(c.x,c.y) if self.cell(x,y).terrain=='grass'}
        self.receipts=[];self.carriers={1:dict(path=[1],value=source_value,masked=False)}

    def send(self,sender,recipient,condition,mode,terminal):
        assert sender.alive and recipient.alive
        assert sender.sleep_until<=self.tick and recipient.sleep_until<=self.tick
        assert abs(sender.x-recipient.x)+abs(sender.y-recipient.y)==1
        parent=self.carriers.get(sender.id)
        reason=None;masked=condition=='masked'
        if condition=='individual':reason='disabled'
        elif not parent:reason='no_source'
        elif condition=='direct' and len(parent['path'])>1:reason='forwarding_disabled'
        elif not masked and parent['value']>=0:reason='nonnegative_source'
        if reason:
            self.receipts.append(dict(sender=sender.id,recipient=recipient.id,delivered=False,reason=reason))
            return
        assert recipient.id not in parent['path'] and len(parent['path'])<8
        key='move:grass' if condition=='irrelevant' and terminal else 'move:hazard'
        packet,value=(None,None) if masked else attenuate(parent['value'],mode,recipient.learned.get(key,0))
        self.carriers[recipient.id]=dict(path=parent['path']+[recipient.id],value=value,masked=masked)
        if not masked:
            recipient.learned[key]=value
            origin=self.origins.setdefault(recipient.id,{}).setdefault(key,origin_record())
            origin.update(social_count=1,last_social_tick=self.tick,last_source=sender.id)
        recipient.memories.append(Episode(self.tick,'hear',recipient.x,recipient.y,
                                          'masked' if masked else key.split(':')[1],packet or 0))
        del recipient.memories[:-64]
        self.receipts.append(dict(sender=sender.id,recipient=recipient.id,delivered=True,
                                  key=key,source_value=parent['value'],packet=packet,acquired=value,
                                  source_xy=[sender.x,sender.y],recipient_xy=[recipient.x,recipient.y],
                                  firsthand_before=0,masked=masked))

    def case(self,source,margin,mode,condition):
        self.reset(source,margin)
        c=self.agents[self.target_id]
        before=scores(self,c)
        baseline=coupled_choice(before,self.rng.getstate())
        for i in range(1,self.depth+1):
            self.send(self.agents[i],self.agents[i+1],condition,mode,i==self.depth)
        acquired=c.learned.get('move:hazard',0)
        readout=execute(self,c,lambda:World.move(self,c),ablate=condition=='ablation')
        after=readout['scores'];chosen=readout['chosen']
        baseline_hazard=self.cell(baseline[1],baseline[2]).terrain=='hazard'
        target=self.carriers.get(c.id)
        delivered=target is not None
        applicable=any(self.cell(x,y).terrain=='hazard' for _,x,y in after) and any(self.cell(x,y).terrain=='grass' for _,x,y in after)
        rank_changed={(x,y) for _,x,y in best(before)}!={(x,y) for _,x,y in best(after)}
        post=digest(dict(template=self.template_digest,
                         agents={i:asdict(self.agents[i]) for i in range(1,self.depth+2)},
                         origins=self.origins,events=[asdict(e) for e in self.events[self._base_events:]],
                         rng=self.rng.getstate()))
        row=dict(seed=self.seed,source=source,actual_source=self.actual_source_value,depth=self.depth,
                 margin=margin,rounding=mode,condition=condition,attempts=self.depth,
                 deliveries=sum(r['delivered'] for r in self.receipts),target_delivered=delivered,
                 acquired_hazard=acquired,firsthand_before=readout['firsthand_before'],
                 score_applicable=applicable and any(a[0]!=b[0] for a,b in zip(before,after)),
                 hazard_warning_applied=acquired!=0 and condition!='ablation',
                 ranking_changed=rank_changed,baseline_hazard=baseline_hazard,
                 hazard_avoided=baseline_hazard and readout['terrain']!='hazard',
                 hazard_increased=not baseline_hazard and readout['terrain']=='hazard',
                 decision_changed=(baseline[1:])!=(chosen[1:]),chosen_x=chosen[1],chosen_y=chosen[2],
                 chosen_terrain=readout['terrain'],before=before,after=after,
                 baseline_choice=baseline,receipts=self.receipts,
                 rng_before=readout['rng_before'],unrelated_before=readout['unrelated_before'],
                 template_digest=self.template_digest,post_digest=post)
        return row
