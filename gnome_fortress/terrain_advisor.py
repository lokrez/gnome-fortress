"""G7's modest terrain extension to the original explicit conditional dialogue."""
from .advisor import Advisor
from .terrain_game import TERRAIN_POWERS


class TerrainAdvisor(Advisor):
    def choices(self):
        if self.page=='main':return super().choices()[:-1]+[('5','What have I done to the land?'),('0','Close')]
        elif self.page=='land':return [('1','Explain latest terrain action'),('2','Open terrain history'),('0','Back')]
        return super().choices()

    def choose(self,choice,world,selected,presentation):
        if choice not in dict(self.choices()):return None
        if self.page=='main' and choice=='5':
            presentation.refresh();self.page='land';s=presentation.land.summary();c=s['conversions'];r=s['requests']
            self.text=(f"Rupture: {r.get('rupture',0)} requests, {c.get('rupture',0)} actual hazard conversions. "
                f"Rewild: {c.get('rewild',0)} forest conversions. Wellspring: {c.get('wellspring',0)} water conversions. "
                f"{s['transitions']} historical transitions across {s['ever_transformed']} distinct tiles. "
                f"{s['currently_altered']} tiles currently differ in terrain from the format-epoch map, sir. "
                "Restoring ground does not rewrite history.")
        elif self.page=='land' and choice!='0':
            presentation.refresh()
            if choice=='1':
                identity=presentation.land.latest
                if identity is None:self.text='No terrain action has completed, sir. Queued requests have not changed the land.'
                else:
                    p=world.interventions[identity-1]
                    self.text=f'#{p.id} {p.kind} completed at tick {p.completed_tick}: {p.changed_cells} changed cells, {p.food_removed} food removed, at ({p.x},{p.y}), radius {p.radius}. No individual survival counterfactual is established, sir.'
            elif choice=='2':return 'terrain'
        elif self.page=='powers' and choice=='2' and world.interventions and world.interventions[-1].kind in TERRAIN_POWERS:
            p=world.interventions[-1]
            self.text=(f'#{p.id} {p.kind}: {p.status}. Requested tick {p.requested_tick}; activates {p.activation_tick}, '
                f'at ({p.x},{p.y}), radius {p.radius}. Actual changed cells: {p.changed_cells}; food removed: {p.food_removed}. '
                'One-shot action; changed terrain persists. This is not evidence of a population benefit, sir.')
        else:return super().choose(choice,world,selected,presentation)
        return None
