"""Replay preregistered natural cases through the real Pygame observer controls."""
import json,os
from pathlib import Path
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import pygame
from gnome_fortress.terrain_game import TerrainWorld
from gnome_fortress.living_viewer import LivingObserver

OUT=Path('docs/g8b/captures');OUT.mkdir(parents=True,exist_ok=True)
EVIDENCE=Path('docs/g8b/evidence')


def main():
    data=json.loads((EVIDENCE/'natural-cases.json').read_text());captures=[]
    for tag in ('movement','drink','eat','learning','hazard_experience','socialize','reproduce','no_slot','death','learned_readout'):
        if tag not in data['cases']:continue
        case=data['cases'][tag];w=TerrainWorld(case['seed'])
        v=LivingObserver(w,paused=True,window_size=(1280,720));v.select_individual(case['identity'])
        v.action('decision-observe');v.toggle_follow()
        for _ in range(case['record']['tick']):
            v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_PERIOD)])
            v.advance(0)
        r=v.current_decision_record()
        assert r==case['record'], f'Natural replay mismatch: {tag}'
        v.draw();pygame.image.save(v.screen,str(OUT/f'{tag}.png'))
        captures.append(dict(file=f'{tag}.png',tick=w.tick,identity=v.selected,
                             decision_tick=r['tick'],driver=os.environ['SDL_VIDEODRIVER'],trace=f'case-{tag}.json'))
        if tag=='movement':
            v.navigate('gnome');v.draw();pygame.image.save(v.screen,str(OUT/'normal-selected.png'))
            v.navigate('decisions');v.decision_details=True;v.draw()
            pygame.image.save(v.screen,str(OUT/'movement-details.png'))
            # Actual 4K surface; borderless solely avoids desktop window decorations
            # constraining the requested test resolution.
            v.screen=pygame.display.set_mode((3840,2160),pygame.NOFRAME);v.layout(v.screen.get_size());v.draw()
            assert v.screen.get_size()==(3840,2160)
            pygame.image.save(v.screen,str(OUT/'decisions-4k.png'))
            captures.extend(dict(file=name,tick=w.tick,identity=v.selected,decision_tick=r['tick'],
                driver=os.environ['SDL_VIDEODRIVER'],trace='case-movement.json')
                for name in ('normal-selected.png','movement-details.png','decisions-4k.png'))
        pygame.quit()
    (EVIDENCE/'captures.json').write_text(json.dumps(dict(captures=captures,human_playtest=False,
        note='Natural case replay through period single-step controls; no inserted events or trace records.'),indent=2)+'\n')


if __name__=='__main__':main()
