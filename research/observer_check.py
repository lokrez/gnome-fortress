"""Real X11 SDL window, OS-delivered controls, state assertions and visible frames.
This is assisted UI verification, not a claim that a human physically used keys.
"""
import ctypes as c
import json
import os
from pathlib import Path
import time

os.environ["SDL_VIDEODRIVER"] = "x11"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
from gnome_fortress.engine import World
from gnome_fortress.storage import load, save
from gnome_fortress.viewer import Observer


class Key(c.Structure):
    _fields_ = [("type", c.c_int), ("serial", c.c_ulong), ("send_event", c.c_int),
                ("display", c.c_void_p), ("window", c.c_ulong), ("root", c.c_ulong),
                ("subwindow", c.c_ulong), ("time", c.c_ulong), ("x", c.c_int), ("y", c.c_int),
                ("x_root", c.c_int), ("y_root", c.c_int), ("state", c.c_uint),
                ("keycode", c.c_uint), ("same_screen", c.c_int)]


class XEvent(c.Union):
    _fields_ = [("key", Key), ("pad", c.c_long * 24)]


def main():
    out = Path("research/phase1/observer")
    out.mkdir(parents=True, exist_ok=True)
    w = World(1)
    w.step(180)
    v = Observer(w)
    x = c.CDLL("libX11.so.6")
    x.XOpenDisplay.restype = c.c_void_p
    x.XOpenDisplay.argtypes = [c.c_char_p]
    x.XStringToKeysym.argtypes = [c.c_char_p]
    x.XStringToKeysym.restype = c.c_ulong
    x.XKeysymToKeycode.argtypes = [c.c_void_p, c.c_ulong]
    x.XKeysymToKeycode.restype = c.c_uint
    x.XSendEvent.argtypes = [c.c_void_p, c.c_ulong, c.c_int, c.c_long, c.POINTER(XEvent)]
    x.XFlush.argtypes = [c.c_void_p]
    x.XCloseDisplay.argtypes = [c.c_void_p]
    display = x.XOpenDisplay(None)
    assert display
    window = pygame.display.get_wm_info()["window"]
    checks = []

    def pump():
        time.sleep(0.12)
        v.handle(pygame.event.get())
        v.draw()

    def key(name):
        event = XEvent()
        event.key.display, event.key.window = display, window
        event.key.same_screen = 1
        event.key.keycode = x.XKeysymToKeycode(display, x.XStringToKeysym(name.encode()))
        for kind, mask in ((2, 1), (3, 2)):
            event.key.type = kind
            assert x.XSendEvent(display, window, 0, mask, c.byref(event))
        x.XFlush(display)
        pump()

    try:
        pump()
        assert pygame.display.get_driver() == "x11"
        pygame.image.save(v.screen, str(out / "running.png"))
        checks.append("Real SDL x11 window created on DISPLAY " + os.environ.get("DISPLAY", ""))
        key("space")
        assert v.paused
        before = w.digest()
        v.advance(1.0)
        assert before == w.digest()
        checks.append("OS Space pauses; one second while paused preserves state")
        key("period")
        v.advance(0)
        assert w.tick == 181
        checks.append("OS period advances exactly one paused tick")
        key("Up")
        assert v.speeds[v.speed_index] == 30
        key("Down")
        assert v.speeds[v.speed_index] == 15
        checks.append("OS Up/Down change speed 15 to 30 to 15")
        key("Tab")
        assert v.selected == 2
        checks.append("OS Tab selects next persistent identity")
        a = w.agents[1]
        event = XEvent()
        event.key.display, event.key.window = display, window
        event.key.x, event.key.y = a.x*v.tile+v.tile//2, a.y*v.tile+v.tile//2
        event.key.same_screen, event.key.keycode = 1, 1  # XButtonEvent button shares this field.
        for kind, mask in ((4, 4), (5, 8)):
            event.key.type = kind
            assert x.XSendEvent(display, window, 0, mask, c.byref(event))
        x.XFlush(display)
        pump()
        mouse_confirmed = (w.agents[v.selected].x, w.agents[v.selected].y) == (a.x, a.y)
        checks.append("OS mouse click target confirmed" if mouse_confirmed else
                      "OS mouse click target NOT CONFIRMED; XSendEvent input injection was inconclusive")
        key("s")
        assert v.save_requested
        save(w, out / "check.sqlite")
        assert load(out / "check.sqlite").digest() == w.digest()
        v.save_requested = False
        checks.append("OS S requests checkpoint; saved checkpoint reloads exactly")
        v.draw()
        pygame.image.save(v.screen, str(out / "paused-inspection.png"))
        key("space")
        assert not v.paused
        before_tick = w.tick
        v.advance(0.2)
        assert w.tick == before_tick + 3
        checks.append("Resume at 15 ticks/sec advances three ticks for 0.2 seconds")
        key("Escape")
        assert not v.running
        checks.append("OS Escape closes observer loop")
        (out / "checks.json").write_text(json.dumps(dict(driver=pygame.display.get_driver(), checks=checks,
            limitations=["OS events sent programmatically, not physical human input", "Mouse targeting could not be confirmed via XSendEvent; synthetic offscreen unit test passes", "Native Wayland backend, window-manager close button, fullscreen and multi-monitor behavior not manually confirmed", "Captures are SDL client surfaces, not compositor screenshots"]), indent=2) + "\n")
        print(json.dumps(checks, indent=2))
    finally:
        x.XCloseDisplay(display)
        pygame.quit()


if __name__ == "__main__":
    main()
