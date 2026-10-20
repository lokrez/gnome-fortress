"""Read-only founder observation. All wall clocks and navigation stay outside World."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import curses
from dataclasses import asdict
import json
import math
from pathlib import Path
import sqlite3
import tempfile
import time
import textwrap

from .engine import World, TRAITS
from .storage import load


def load_snapshot(path, loader=load):
    """Never invoke the recovery-capable loader against a research archive."""
    path = Path(path).expanduser().resolve(strict=True)
    # WAL may need writable shared-memory files. Hot journals need recovery.
    # Refuse both rather than opening a preserved archive with write privileges.
    if any(Path(str(path) + suffix).exists() for suffix in ('-wal', '-journal')):
        raise ValueError('Checkpoint has a WAL/journal; use a clean, closed checkpoint copy.')
    with path.open('rb') as source:
        header = source.read(100)
    if len(header) < 100 or header[:16] != b'SQLite format 3\x00':
        raise ValueError('Not a complete SQLite checkpoint')
    if header[18:20] != b'\x01\x01':
        raise ValueError('Only closed rollback-mode checkpoints are supported; export a clean copy.')
    with tempfile.TemporaryDirectory(prefix='gnome-observatory-') as directory:
        copy = Path(directory) / 'snapshot.sqlite'
        with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=1)) as source:
            with closing(sqlite3.connect(copy)) as destination:
                source.backup(destination, pages=256, sleep=.01)
        return loader(copy)


def status(agent, tick):
    if not agent.alive:
        return 'DEAD'
    return 'SLEEP' if agent.sleep_until > tick else 'ALIVE'


class Observation:
    """Presentation state only; cached history indexes consume no random numbers."""
    def __init__(self, world, live=True):
        self.world = world
        self.founders = tuple(sorted(a.id for a in world.agents.values() if not a.parents))
        if len(self.founders) != 60:
            raise ValueError(f'Expected 60 founder records, found {len(self.founders)}')
        self.selected = 0
        self.population = "founders"
        self.roster = self.founders
        self.offset = 0
        self.paused = True
        self.live = live
        self.rate = 10.0
        self.refresh = 5.0
        self.births = self.deaths = 0
        self._event_cursor = 0
        self._recent = {a.id: [] for a in world.agents.values() if not a.parents or a.alive}
        self._index_events()

    def _index_events(self):
        for index in range(self._event_cursor, len(self.world.events)):
            event = self.world.events[index]
            self.births += event.kind == 'birth' and not event.detail.get('founder', False)
            self.deaths += event.kind == 'death'
            if event.kind == 'birth' and self.world.agents[event.actor].alive:
                self._recent.setdefault(event.actor, [])
            for identity in {event.actor, event.target} & self._recent.keys():
                records = self._recent[identity]
                records.append(event)
                del records[:-12]
        self._event_cursor = len(self.world.events)

    def refresh_roster(self):
        if self.population == 'founders':
            return
        identity = self.roster[self.selected] if self.roster else None
        self.roster = tuple(sorted(a.id for a in self.world.living() if a.parents))
        if identity in self.roster:
            self.selected = self.roster.index(identity)
        else:
            self.selected = min(self.selected, max(0, len(self.roster)-1))

    def select_population(self, population):
        if population not in ('founders', 'descendants'):
            raise ValueError('Unknown observational roster')
        self.population = population
        self.roster = self.founders if population == 'founders' else ()
        self.selected = self.offset = 0
        self.refresh_roster()

    def navigate(self, delta):
        self.refresh_roster()
        if self.roster:
            self.selected = (self.selected + delta) % len(self.roster)
        self.offset = 0

    def toggle(self):
        if self.live:
            self.paused = not self.paused

    def step(self):
        if self.live and self.paused:
            self.world.step()

    def advance(self, count):
        if self.live and not self.paused:
            self.world.step(count)

    def persona(self):
        self._index_events()
        self.refresh_roster()
        w = self.world
        if not self.roster:
            return ['No living descendants yet.', 'Founders remain available with f.']
        a = w.agents[self.roster[self.selected]]
        available = lambda name: getattr(a, name, 'unavailable')
        result = [f'{a.name} | ID {a.id} | {status(a, w.tick)}',
                  f'Parents: {a.parents or "none (founder)"} | born tick {a.born}',
                  f'Children count: {available("children")}',
                  f'Age: {a.age} ticks (includes age at entry)',
                  f'Death tick: {a.died} | cause: {a.death_cause or "none recorded"}',
                  f'Location: ({a.x}, {a.y}) | health: {a.health}',
                  f'Hunger: {a.hunger} | thirst: {a.thirst} | fatigue: {a.fatigue}',
                  f'Sleep until: {a.sleep_until} | cooldown: {available("cooldown")}',
                  f'Latest action: {available("action")}',
                  'Deceased values are retained terminal state.' if not a.alive else 'Biological values are current state.',
                  '', 'INHERITED TRAITS (0-100; founders sampled 20-80)']
        result += [f'{trait}: {a.traits.get(trait, "unavailable")}' for trait in TRAITS]
        result += ['', 'VALUE SUMMARY (programmed tendencies, not diagnoses)',
                   f'Novelty weight curiosity={a.traits.get("curiosity", "unavailable")};',
                   f'hazard aversion caution={a.traits.get("caution", "unavailable")}.',
                   'Other traits govern social/reproduction propensity,',
                   'age limit and sensory radius; no inferred biography.',
                   '', 'SCHEDULER (founders are not slots)',
                   f'Assigned slot indexes (0-based): {[i for i, identity in enumerate(w.slots) if identity == a.id]}',
                   f'Eligible: {a.alive and a.sleep_until <= w.tick} | cursor: {w.cursor}',
                   'Assignments are retained snapshots, not decision counts.',
                   '', 'LEARNED ASSOCIATIONS (-100..100)']
        learned = getattr(a, 'learned', None)
        result += [f'{key}: {value}' for key, value in sorted((learned or {}).items())] or ['None recorded / unavailable']
        result += ['Only move:* associations influence movement scoring.']
        if hasattr(w, 'origins'):
            result += ['', f'COMMUNICATION EXPERIMENT: {w.config.condition}',
                       'Association strengths are not probabilities of truth.',
                       'KNOWLEDGE ORIGINS (firsthand versus socially acquired)']
            records = w.origins.get(a.id, {})
            result += [f'{key}: {json.dumps(origin, sort_keys=True)}'
                       for key, origin in sorted(records.items())] or ['None recorded']
            result += ['hear episodes are received messages, not physical experiences.']
        result += ['', 'EPISODIC MEMORY (latest 64 retained)']
        memories = getattr(a, 'memories', None)
        result += [json.dumps(asdict(memory), sort_keys=True) for memory in reversed(memories or [])] or ['None recorded / unavailable']
        result += ['', 'DIRECTIONAL RELATIONSHIPS (outgoing, 0-100)']
        relations = getattr(a, 'relationships', None)
        result += [f'ID {identity}: {value}' for identity, value in sorted((relations or {}).items())] or ['None recorded / unavailable']
        visits = getattr(a, 'visits', None)
        result += ['', f'Visited locations: {len(visits) if visits is not None else "unavailable"}',
                   '', 'RECENT SIGNIFICANT EVENTS (actor/target match; latest 12)']
        result += [f'{e.tick} {e.kind} actor={e.actor} target={e.target} {json.dumps(e.detail, sort_keys=True)}'
                   for e in reversed(self._recent.get(a.id, []))] or ['None recorded']
        result += ['Complete decision history: unavailable. No invented persona fields.']
        return result

    def layout(self, width, height, performance=''):
        """ASCII rows: small terminals scroll the roster to keep selection visible."""
        width, height = max(1, width), max(1, height)
        self._index_events()
        self.refresh_roster()
        w = self.world
        header = [f"FOUNDERS' OBSERVATORY | tick {w.tick} | {'PAUSED' if self.paused else 'RUNNING'}",
                  f'Living {len(w.living())} | births {self.births} (excludes founders) | deaths {self.deaths}',
                  f'{len(w.slots)} slots | rate {self.rate:g} ticks/s | refresh {self.refresh:g} Hz | {performance}']
        wide = width >= 110 and height >= 17
        grid_width = 42 if wide else width
        cell_width = max(7, len(str(max(self.roster, default=60)))+5)
        columns = max(1, min(6, grid_width // cell_width))
        rows = max(1, math.ceil(len(self.roster) / columns))
        room = max(1, height - 5 if wide else min(rows, max(1, (height - 4) // 2)))
        first = max(0, min(self.selected // columns - room + 1, rows - room))
        grid = []
        for row in range(first, min(rows, first + room)):
            cells = []
            for index in range(row * columns, min(len(self.roster), (row + 1) * columns)):
                a = w.agents[self.roster[index]]
                marker = {'ALIVE': 'A', 'SLEEP': 'S', 'DEAD': 'D'}[status(a, w.tick)]
                cells.append(f'{">" if index == self.selected else " "}{a.id:02d}:{marker} '.ljust(cell_width-1))
            grid.append(' '.join(cells))
        roster_label = '60 original founders' if self.population == 'founders' else f'{len(self.roster)} living descendants'
        label = f'{roster_label} A=alive S=sleep D=dead | rows {first+1}-{min(rows,first+room)}/{rows}'
        detail_width = max(1, width - 44) if wide else width
        detail = [piece for line in self.persona() for piece in (textwrap.wrap(line, detail_width, replace_whitespace=False) or [''])]
        detail_room = max(1, height - 5 if wide else height - len(header) - len(grid) - 3)
        self.offset = min(max(0, self.offset), max(0, len(detail) - detail_room))
        visible = detail[self.offset:self.offset + detail_room]
        if wide:
            body = [f'{grid[i] if i < len(grid) else "":42} | {visible[i] if i < len(visible) else ""}'
                    for i in range(max(len(grid), len(visible)))]
        else:
            body = grid + [f'Inspector ID {self.roster[self.selected] if self.roster else "none"} (PgUp/PgDn)'] + visible
        footer = 'f founders / l living descendants | Arrows/Tab select | PgUp/Dn | Space pause | . step | +/- | [/] | q'
        return [line[:width].rstrip() for line in (header + [label] + body + [footer])[:height]]


def run(screen, future, live, rate, refresh):
    curses.set_escdelay(25)
    screen.nodelay(True)
    screen.keypad(True)
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    view = None
    previous = None
    due = time.monotonic()
    draw_due = due
    sample_time = due
    sample_tick = 0
    performance = '0.0 actual ticks/s'
    error = None
    while True:
        key = screen.getch()
        if key in (ord('q'), 27):
            return
        if view is None and error is None and future.done():
            try:
                view = future.result()
                view.live, view.rate, view.refresh = live, rate, refresh
                due = sample_time = time.monotonic()
                sample_tick = view.world.tick
            except Exception as exc:
                error = f'{type(exc).__name__}: {exc}'
        now = time.monotonic()
        h, width = screen.getmaxyx()
        if view is not None:
            view.refresh_roster()
            cell_width = max(7, len(str(max(view.roster, default=60)))+5)
            cols = max(1, min(6, (42 if width >= 110 and h >= 17 else width) // cell_width))
            if key in (curses.KEY_RIGHT, 9): view.navigate(1)
            elif key == curses.KEY_LEFT: view.navigate(-1)
            elif key == curses.KEY_DOWN: view.navigate(cols)
            elif key == curses.KEY_UP: view.navigate(-cols)
            elif key == ord('f'): view.select_population('founders')
            elif key == ord('l'): view.select_population('descendants')
            elif key == curses.KEY_NPAGE: view.offset += max(1, h // 2)
            elif key == curses.KEY_PPAGE: view.offset -= max(1, h // 2)
            elif key == ord(' '): view.toggle(); due = now
            elif key == ord('.'): view.step(); due = now
            elif key in (ord('+'), ord('=')): view.rate = min(1000, view.rate * 2); due = now
            elif key == ord('-'): view.rate = max(.25, view.rate / 2); due = now
            elif key == ord(']'): view.refresh = min(30, view.refresh * 2)
            elif key == ord('['): view.refresh = max(1, view.refresh / 2)
            deadline = time.monotonic() + .008
            while view.live and not view.paused and now >= due and time.monotonic() < deadline:
                view.advance(1)
                due += 1 / view.rate
            if view.paused or not view.live:
                due = now
            due = max(due, now - 1)  # bound pacing debt; never skip simulation ticks
            if now - sample_time >= 1:
                performance = f'{(view.world.tick-sample_tick)/(now-sample_time):.1f} actual ticks/s'
                sample_tick, sample_time = view.world.tick, now
            if key != -1 or now >= draw_due:
                lines = view.layout(width, h, performance + (' | READ ONLY' if not view.live else ' | UNSAVED'))
                draw_due = now + 1 / view.refresh
            else:
                lines = previous
        else:
            lines = ["FOUNDERS' OBSERVATORY", error or 'Loading read-only checkpoint / indexing founders...', 'q quit (loading worker finishes before exit)']
        if lines != previous:
            screen.erase()
            for row, line in enumerate(lines or []):
                if row >= h: break
                try:
                    screen.addnstr(row, 0, line, max(0, width - 1))
                except curses.error:
                    pass
            screen.refresh()
            previous = lines
        # sleep releases the GIL so the checkpoint worker can actually load.
        time.sleep(.02 if view and not view.paused else .05)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, help='Read-only source; never saved or overwritten')
    parser.add_argument('--seed', type=int, default=1)
    parser.add_argument('--communication', choices=('individual', 'social', 'sham'),
                        help='Explicit Phase 4A experiment; required for its checkpoint format')
    parser.add_argument('--live', action='store_true', help='Allow stepping a loaded copy (no persistence)')
    parser.add_argument('--rate', type=float, default=10)
    parser.add_argument('--refresh', type=float, default=5)
    args = parser.parse_args()
    if not math.isfinite(args.rate) or not .25 <= args.rate <= 1000:
        parser.error('--rate must be finite and between .25 and 1000')
    if not math.isfinite(args.refresh) or not 1 <= args.refresh <= 30:
        parser.error('--refresh must be finite and between 1 and 30')
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='observatory-load') as pool:
        def create_observation():
            if args.communication:
                from .communication import CommunicationConfig, CommunicationWorld, load_experiment
                world = (load_snapshot(args.checkpoint, loader=load_experiment) if args.checkpoint
                         else CommunicationWorld(args.seed, CommunicationConfig(args.communication)))
                if world.config.condition != args.communication:
                    raise ValueError('Checkpoint communication condition does not match requested condition')
            else:
                world = load_snapshot(args.checkpoint) if args.checkpoint else World(args.seed)
            return Observation(world)
        future = pool.submit(create_observation)
        try:
            curses.wrapper(run, future, bool(args.live or not args.checkpoint), args.rate, args.refresh)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
