import os,threading
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import pygame
from gnome_fortress.engine import World
from gnome_fortress import viewer


def test_observer_services_controls_while_writer_holds_world(tmp_path,monkeypatch):
    release=threading.Event();seen=[];w=World()
    class Observer(viewer.Observer):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.save_requested=True;self.controls=0
        def handle(self,events):
            super().handle(events)
            for e in events:
                if e.type==pygame.KEYDOWN and e.key==pygame.K_TAB:
                    self.controls+=1;seen.append(('control',self.world.tick))
            if self.controls==3:release.set();self.running=False
    def slow_save(world,path):
        import time
        tick=world.tick
        assert threading.current_thread() is not threading.main_thread()
        for _ in range(3):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_TAB));time.sleep(.05)
        assert release.wait(2),'observer did not service controls during write'
        assert world.tick==tick
        seen.append(('saved',tick))
    monkeypatch.setattr(viewer,'Observer',Observer)
    viewer.run(w,tmp_path/'state.sqlite',slow_save,paused=True,max_frames=30)
    assert len([s for s in seen if s[0]=='control'])==3
    assert any(s[0]=='saved' for s in seen) and w.tick==0


def test_paused_loop_sleeps_and_avoids_repeated_redraw(tmp_path,monkeypatch):
    ticks=[];draws=[]
    class Clock:
        def tick(self,hz):ticks.append(hz);return 100
    class Observer(viewer.Observer):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);pygame.event.clear()
        def draw(self):draws.append(self.world.tick)
    monkeypatch.setattr(viewer,'Observer',Observer)
    monkeypatch.setattr(pygame.time,'Clock',Clock)
    w=World();viewer.run(w,tmp_path/'idle.sqlite',lambda *a:None,paused=True,max_frames=5)
    assert ticks==[10]*5 and draws==[0] and w.tick==0


def test_speed_change_clears_overload_debt():
    w=World();v=viewer.Observer(w)
    try:
        v.accumulator=10000
        v.handle([pygame.event.Event(pygame.KEYDOWN,key=pygame.K_MINUS)])
        assert v.accumulator==0
        v.advance(0)
        assert w.tick==0
    finally:pygame.quit()
