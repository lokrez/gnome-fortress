"""Scripted, ephemeral presentation. No world writes, RNG or NPC entity."""
from .life_presentation import life_summary


class Advisor:
    def __init__(self):
        self.open=False
        self.page='main'
        self.text='How may I assist you, sir?'

    def start(self):
        self.open=True
        self.page='main'
        self.text='How may I assist you, sir?'

    def choices(self):
        if self.page=='main':
            return [('1','How are my gnomes?'),('2','Tell me about this gnome.'),
                    ('3','What have my divine powers done?'),('4','I have a complaint.'),('0','Close')]
        elif self.page=='world':
            return [('1','Show population statistics'),('2','Show recent deaths'),('3','Open global recorded events'),('0','Back')]
        elif self.page=='gnome':
            return [('1','Open Life'),('2','Open Direct Family'),('0','Back')]
        elif self.page=='powers':
            return [('1','Open intervention records'),('2','Explain latest intervention'),('0','Back')]
        else:
            return [('1',"Who's responsible for this mess?"),('2','Why are you always correcting me?'),
                    ('3','Where is the mountain lion?'),('0','Back')]

    def choose(self,choice,world,selected,presentation):
        if choice not in dict(self.choices()):
            return None
        if choice=='0':
            if self.page=='main':self.open=False
            else:self.start()
            return None
        presentation.refresh()
        if self.page=='main':
            if choice=='1':
                self.page='world'
                self.text=f"There are {presentation.status['living']} living gnomes, sir. We began with 60 founders."
            elif choice=='2':
                self.page='gnome';a=life_summary(world,selected)
                if a is None:self.text='No selected individual record is available, sir.'
                elif a['status']=='deceased':
                    self.text=f"Gnome {a['id']:05d} died: {a['death_cause'] or 'cause unavailable'}, at tick {a['died']}. Recorded age {a['age']}, sir."
                else:self.text=f"Gnome {a['id']:05d} is {a['status']}, sir. Recorded age {a['age']}; health {a['health']}."
            elif choice=='3':
                self.page='powers'
                self.text=f'{len(world.interventions)} divine requests are recorded, sir. Resource changes are measurable; population benefits are not established.' if world.interventions else 'No divine interventions are recorded, sir. Restraint is also an option.'
            elif choice=='4':
                self.page='complaints';self.text='Complaints department, sir. Please select the nature of your concern.'
        elif self.page=='world':
            if choice=='1':return 'statistics'
            elif choice=='2':
                deaths=[]
                for position in reversed(presentation.events.positions):
                    e=world.events[position]
                    if e.kind=='death':
                        deaths.append(f"Tick {e.tick}: Gnome {e.actor:05d}, {e.detail.get('cause','unavailable')}.")
                        if len(deaths)==5:break
                self.text='Latest recorded deaths: '+ ' '.join(deaths) if deaths else 'No deaths are recorded, sir.'
            elif choice=='3':return 'events'
        elif self.page=='gnome':
            if choice=='1':return 'life'
            elif choice=='2':return 'family'
        elif self.page=='powers':
            if choice=='1':return 'powers'
            elif choice=='2':
                if not presentation.powers:self.text='No divine interventions are recorded, sir.'
                else:
                    p=presentation.powers[-1];t=p['totals']
                    overlap=f" Current producing-cell coverage: {p['overlap']}." if p['overlap'] else ''
                    self.text=(f"#{p['id']} {p['kind']}: {p['status']}, at {p['location']}, radius {p['radius']}. "
                        f"Activates {p['activation']}; expires {p['expires']}; {p['future_active_ticks']} active ticks ahead."
                        +overlap+f" Regenerated {t['regenerated']}; ordinary regeneration on the same pre-pulse stocks {t['normal_regeneration']}; delta {t['delta']:+d}. "
                        f"Recorded overridden producing-cell pulses: {t['overridden_cells']}. This does not establish a cause of death or a survival benefit, sir.")
        else:
            if choice=='1':self.text='You are the governing deity, sir.'
            elif choice=='2':self.text='You appointed me to provide accurate information, sir.'
            elif choice=='3':self.text='We have not implemented mountain lions, sir.'
        return None
