import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
import pytest
from gnome_fortress.advisor import Advisor
from gnome_fortress.game import GameWorld
from gnome_fortress.game_presentation import WorldPresentation
from gnome_fortress.god_viewer import GodObserver
from gnome_fortress.game_storage import save_game,load_game


def key(k):return pygame.event.Event(pygame.KEYDOWN,key=k)


def test_all_choices_and_invalid_back_close():
    w=GameWorld();p=WorldPresentation(w);a=Advisor();a.start();before=w.state()
    for topic in '1234':
        a.start();a.choose(topic,w,1,p);page=a.page
        for choice,_ in a.choices():
            if choice=='0':continue
            a.choose(choice,w,1,p)
            assert a.text and a.page==page
        old=a.text;a.choose('999',w,1,p);assert a.text==old
        a.choose('0',w,1,p);assert a.page=='main' and a.open
    a.choose('0',w,1,p);assert not a.open
    assert w.state()==before


def test_world_live_deaths_and_selection_facts():
    w=GameWorld();p=WorldPresentation(w);a=Advisor()
    a.choose('1',w,1,p);assert '60 living' in a.text
    a.choose('2',w,1,p);assert 'No deaths' in a.text
    w.kill(w.agents[1],'hazard');a.start();a.choose('1',w,1,p)
    assert '59 living' in a.text
    a.choose('2',w,1,p);assert 'Tick 0: Gnome 00001, hazard' in a.text
    a.start();a.choose('2',w,1,p);assert 'died: hazard, at tick 0' in a.text
    for identity,status in ((2,'awake'),(3,'sleeping')):
        if identity==3:w.agents[3].sleep_until=10
        a.start();a.choose('2',w,identity,p);assert status in a.text and 'died' not in a.text
    a.start();a.choose('2',w,None,p);assert 'No selected' in a.text


def test_intervention_truth_and_lifecycle():
    w=GameWorld();p=WorldPresentation(w);a=Advisor()
    a.choose('3',w,1,p);assert 'No divine' in a.text
    a.choose('2',w,1,p);assert 'No divine' in a.text
    w.request('rain',20,16,5,20);w.request('rain',20,16,5,20)
    a.choose('2',w,1,p);assert '#2 rain: queued' in a.text and 'overridden.' not in a.text
    w.step(10);a.choose('2',w,1,p)
    assert 'Current producing-cell coverage: overridden.' in a.text
    t=w.interventions[-1].totals
    assert f"delta {t['delta']:+d}" in a.text and str(t['overridden_cells']) in a.text
    w.request('drought',20,16,5,2);w.step()
    a.choose('2',w,1,p);assert '#3 drought: active' in a.text
    w.step(2);a.choose('2',w,1,p);assert '#3 drought: expired' in a.text
    assert 'Current producing-cell coverage:' not in a.text


@pytest.mark.parametrize('topic,choice,tab,pane', [('1','1','gnome','events'),('1','3','gnome','events'),('2','1','life','events'),('2','2','life','family'),('3','1','powers','events')])
def test_navigation_mouse_keys_preserve_watch(topic,choice,tab,pane):
    w=GameWorld();v=GodObserver(w,paused=True);v.watch_id=1;before=w.state()
    try:
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=v.advisor_button.center)])
        v.handle([key(pygame.K_0+int(topic))]);v.draw()
        rect=next(r for r,c in v.advisor_hits if c==choice)
        v.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=rect.center)])
        assert not v.advisor.open and v.tab==tab and v.life_pane==pane
        assert v.selected==v.watch_id==1 and w.state()==before
    finally:pygame.quit()


def test_dialogue_render_cadence_checkpoint_and_controls(tmp_path):
    a=GameWorld(3);b=GameWorld(3);a.request('rain',20,16);b.request('rain',20,16)
    v=GodObserver(b,paused=True)
    try:
        for tick in range(40):
            for _ in range(tick%3+1):
                before=b.state();v.handle([key(pygame.K_a),key(pygame.K_3),key(pygame.K_2)])
                v.draw();v.handle([key(pygame.K_a)])
                assert b.state()==before
            a.step();v.handle([key(pygame.K_PERIOD)]);v.advance(0)
        assert a.state()==b.state()
        path=tmp_path/'advisor.g1.sqlite';save_game(b,path);c=load_game(path)
        c.step(10);a.step(10);assert c.state()==a.state()
        v.handle([key(pygame.K_a),key(pygame.K_s)]);assert v.save_requested
        v.handle([key(pygame.K_ESCAPE)]);assert not v.running
    finally:pygame.quit()


def test_complaints_and_small_panel_and_extinction():
    w=GameWorld();v=GodObserver(w,paused=True)
    try:
        v.screen=pygame.display.set_mode((v.map_width+470,600))
        for topic in '1234':
            v.advisor.start();v.advisor_choice(topic);v.draw()
            assert all(r.bottom<582 for r,_ in v.advisor_hits)
        for choice,phrase in [('1','governing deity'),('2','accurate information'),('3','not implemented mountain lions')]:
            v.advisor_choice(choice);assert phrase in v.advisor.text
        for agent in list(w._living_agents.values()):w.kill(agent,'hazard')
        v.advisor.start();v.advisor_choice('1');v.draw();v.advance(1)
        assert '0 living' in v.advisor.text and w.tick==0 and v.paused
    finally:pygame.quit()
