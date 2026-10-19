"""Fast observation/control tests; no changes to biological rules."""
from concurrent.futures import Future
import curses
import hashlib

import pytest

from gnome_fortress.engine import World
from gnome_fortress.observatory import Observation, load_snapshot, run, status
from gnome_fortress.storage import save


def test_exact_founders_persistent_selection_and_real_fields():
    w = World(42)
    view = Observation(w)
    assert view.founders == tuple(range(1, 61))
    assert view.founders == Observation(World(42)).founders
    child = w._spawn(1, 1, w.agents[1].traits, (1, 2))
    w.kill(w.agents[1], 'test')
    assert len(view.founders) == 60 and child.id not in view.founders
    text = '\n'.join(view.persona())
    for field in ('ID 1', 'DEAD', 'Parents:', 'curiosity:', 'caution:', 'sociability:',
                  'fertility:', 'stamina:', 'vision:', 'Location:', 'health:',
                  'Hunger:', 'thirst:', 'fatigue:', 'LEARNED', 'MEMORY', 'RELATIONSHIPS', 'SCHEDULER'):
        assert field in text
    view.navigate(59)
    assert view.founders[view.selected] == 60
    view.navigate(1)
    assert view.selected == 0


def test_status_missing_optional_and_directional_history():
    w = World()
    a = w.agents[1]
    assert status(a, w.tick) == 'ALIVE'
    a.sleep_until = 5
    assert status(a, w.tick) == 'SLEEP'
    a.learned = {'move:hazard': -13}
    a.relationships[2] = 7
    w.remember(a, 'move', 'grass', 4)
    view = Observation(w)
    text = '\n'.join(view.persona())
    assert 'move:hazard: -13' in text and 'ID 2: 7' in text
    w.kill(a, 'test')
    assert status(a, w.tick) == 'DEAD'
    assert 'death actor=1' in '\n'.join(view.persona())
    # Missing optional presentation fields must not invent replacements.
    a.learned = a.memories = a.relationships = a.visits = None
    assert 'unavailable' in '\n'.join(view.persona())


@pytest.mark.parametrize('size', [(140, 35), (80, 24), (30, 12), (8, 5), (1, 1)])
def test_resize_scroll_keeps_every_founder_reachable(size):
    view = Observation(World())
    width, height = size
    for index in range(60):
        view.selected = index
        lines = view.layout(width, height)
        assert len(lines) <= height
        assert all(len(line) <= width for line in lines)
        if width >= 30 and height >= 12:
            assert f'>{index+1:02d}:A' in '\n'.join(lines)
    view.offset = 100000
    assert view.layout(width, height)


@pytest.mark.parametrize('size', [(140, 35), (80, 24)])
def test_overview_has_sixty_cells_together(size):
    text = '\n'.join(Observation(World()).layout(*size))
    assert all(f'{identity:02d}:A' in text for identity in range(1, 61))


def test_viewing_alone_is_pure_and_pause_step_matches_reference():
    w, reference = World(2026), World(2026)
    view = Observation(w)
    original = w.state()
    for i in range(60):
        view.navigate(1)
        view.persona()
        view.layout(80, 24)
    assert w.state() == original
    view.advance(10)
    assert w.tick == 0
    view.step()
    assert w.tick == 1
    view.toggle()
    view.step()  # no unrequested single-step during running
    view.advance(99)
    reference.step(100)
    assert w.state() == reference.state()
    view.toggle()
    view.advance(10)
    assert w.tick == 100
    frozen = Observation(w, live=False)
    frozen.toggle(); frozen.step(); frozen.advance(10)
    assert frozen.paused and w.state() == reference.state()


def test_checkpoint_readonly_legacy_and_current(tmp_path):
    from research.phase3.reference.storage import save as legacy_save
    from research.phase3.reference.engine import World as LegacyWorld
    for writer, w, name in [(save, World(3), 'current'), (legacy_save, LegacyWorld(3), 'legacy')]:
        w.step(5)
        path = tmp_path / f'{name}.sqlite'
        writer(w, path)
        digest = hashlib.sha256(path.read_bytes()).digest()
        path.chmod(0o444)
        loaded = load_snapshot(path)
        assert loaded.state() == w.state()
        assert 'ID 1' in '\n'.join(Observation(loaded, live=False).persona())
        assert hashlib.sha256(path.read_bytes()).digest() == digest
        assert not list(tmp_path.glob('*-journal'))


def test_refuses_missing_corrupt_and_journal_inputs(tmp_path):
    missing = tmp_path / 'missing.sqlite'
    with pytest.raises(FileNotFoundError): load_snapshot(missing)
    assert not missing.exists()
    missing.write_bytes(b'broken')
    with pytest.raises(ValueError): load_snapshot(missing)
    missing.unlink()
    save(World(), missing)
    journal = tmp_path / 'missing.sqlite-journal'
    journal.write_bytes(b'preserve')
    before = missing.read_bytes()
    with pytest.raises(ValueError, match='WAL/journal'): load_snapshot(missing)
    assert journal.read_bytes() == b'preserve' and missing.read_bytes() == before


class Screen:
    def __init__(self, keys):
        self.keys = iter(keys)
        self.frames = []
        self.lines = []
    def nodelay(self, value): pass
    def keypad(self, value): pass
    def getch(self): return next(self.keys)
    def getmaxyx(self): return 35, 140
    def erase(self): self.lines = []
    def addnstr(self, row, col, line, count): self.lines.append(line[:count])
    def refresh(self): self.frames.append(tuple(self.lines))


def test_curses_controls_and_loading_responsiveness(monkeypatch):
    monkeypatch.setattr('gnome_fortress.observatory.time.sleep', lambda _: None)
    monkeypatch.setattr(curses, 'curs_set', lambda _: None)
    future = Future()
    screen = Screen([-1, -1, ord('q')])
    run(screen, future, False, 10, 5)
    assert len(screen.frames) == 1
    assert 'Loading' in '\n'.join(screen.frames[0])
    view = Observation(World())
    future.set_result(view)
    screen = Screen([ord('.'), curses.KEY_RIGHT, curses.KEY_NPAGE,
                     ord('+'), ord(']'), ord('q')])
    run(screen, future, True, 10, 5)
    assert view.world.tick == 1 and view.selected == 1 and view.offset > 0
    assert view.rate == 20 and view.refresh == 10
    assert any('ID 2' in '\n'.join(frame) for frame in screen.frames)


def test_paused_no_repeated_redraw(monkeypatch):
    sleeps = []
    monkeypatch.setattr('gnome_fortress.observatory.time.sleep', sleeps.append)
    monkeypatch.setattr(curses, 'curs_set', lambda _: None)
    future = Future(); view = Observation(World()); future.set_result(view)
    screen = Screen([-1, -1, -1, ord('q')])
    run(screen, future, True, 10, 5)
    assert view.world.tick == 0 and len(screen.frames) == 1
    assert sleeps == [.05, .05, .05]


def test_live_curses_ticks_match_engine_independent_of_display(monkeypatch):
    import gnome_fortress.observatory as module
    clock = [0.0]
    monkeypatch.setattr(module.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr('gnome_fortress.observatory.time.sleep', lambda delay: clock.__setitem__(0, clock[0] + delay))
    monkeypatch.setattr(curses, 'curs_set', lambda _: None)
    outcomes = []
    for refresh in (1, 30):
        clock[0] = 0
        w = World(42)
        future = Future(); future.set_result(Observation(w))
        screen = Screen([ord(' ')] + [-1] * 30 + [ord('q')])
        run(screen, future, True, 10, refresh)
        assert w.tick > 0
        reference = World(42); reference.step(w.tick)
        assert w.state() == reference.state()
        outcomes.append(w.state())
    assert outcomes[0] == outcomes[1]


def test_real_terminal_load_worker_and_resize(tmp_path):
    from research.observatory.capture import capture
    path = tmp_path / 'checkpoint.sqlite'
    save(World(7), path)
    before = path.read_bytes()
    result = capture(path, output_directory=tmp_path, load_timeout=5)
    assert result['roster_rendered'] and result['exit_code'] == 0
    assert not result['traceback']
    assert path.read_bytes() == before
