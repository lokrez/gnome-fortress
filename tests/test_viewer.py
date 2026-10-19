import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest

pygame = pytest.importorskip("pygame")

from gnome_fortress.engine import World
from gnome_fortress.viewer import Observer, run


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_controls_and_render_do_not_change_world():
    w = World(1)
    viewer = Observer(w)
    try:
        before = w.digest()
        viewer.draw()
        viewer.handle([key(pygame.K_SPACE)])
        viewer.advance(1.0)
        assert viewer.paused and w.digest() == before
        viewer.handle([key(pygame.K_PERIOD)])
        viewer.advance(0)
        assert w.tick == 1
        old_speed = viewer.speed_index
        viewer.handle([key(pygame.K_PLUS)])
        assert viewer.speed_index == old_speed + 1
        viewer.handle([key(pygame.K_MINUS), key(pygame.K_TAB), key(pygame.K_s)])
        assert viewer.selected == 2 and viewer.save_requested
        a = w.agents[1]
        viewer.handle([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                          pos=(a.x*viewer.tile+1, a.y*viewer.tile+1))])
        assert w.agents[viewer.selected].x == a.x
        viewer.draw()
        viewer.handle([key(pygame.K_SPACE)])
        viewer.advance(0.1)
        assert w.tick == 2
        control = World(1)
        control.step(2)
        assert w.digest() == control.digest()
        viewer.handle([pygame.event.Event(pygame.QUIT)])
        assert not viewer.running
    finally:
        pygame.quit()


def test_render_dead_and_sleeping_agents():
    w = World(2)
    w.kill(w.agents[1], "test")
    w.agents[2].sleep_until = 12
    v = Observer(w)
    try:
        v.selected = 1
        v.draw()
        v.selected = 2
        v.draw()
    finally:
        pygame.quit()


def test_bounded_observer_loop(tmp_path):
    saves = []
    run(World(), tmp_path / "test.sqlite", lambda w, p: saves.append(w.tick), max_frames=2)
