"""Pygame observer. Wall-clock pacing never enters simulation state."""
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame
import time

from .runtime import CheckpointWorker, Statistics, checkpoint_notice

COLORS = {"grass": (47, 67, 49), "forest": (29, 52, 39), "rock": (89, 92, 94),
          "water": (34, 89, 126), "hazard": (125, 54, 47)}


class Observer:
    def __init__(self, world, rate=None, paused=False):
        pygame.display.init()
        pygame.font.init()
        self.world = world
        self.tile = max(8, min(20, 900 // world.width, 680 // world.height))
        self.map_width = world.width * self.tile
        self.screen = pygame.display.set_mode((self.map_width + 390, max(680, world.height*self.tile)))
        pygame.display.set_caption("Gnome Fortress | deterministic artificial life")
        self.font = pygame.font.Font(None, 21)
        self.small = pygame.font.Font(None, 18)
        self.paused = paused
        self.saving = False
        self.speeds = [1, 5, 15, 30, 60, 120, 300]
        self.speed_index = 2
        if rate is not None:
            if rate not in self.speeds: self.speeds = sorted(self.speeds + [rate])
            self.speed_index = self.speeds.index(rate)
        self.selected = 1
        self.running = True
        self.accumulator = 0.0
        self.single_step = False
        self.save_requested = False

    def handle(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    self.accumulator = 0.0
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_UP):
                    self.speed_index = min(len(self.speeds)-1, self.speed_index+1)
                    self.accumulator = 0.0
                elif event.key in (pygame.K_MINUS, pygame.K_DOWN):
                    self.speed_index = max(0, self.speed_index-1)
                    self.accumulator = 0.0
                elif event.key == pygame.K_PERIOD:
                    self.single_step = True
                elif event.key == pygame.K_s:
                    self.save_requested = True
                elif event.key == pygame.K_TAB:
                    self.selected = self.selected % len(self.world.agents) + 1
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos
                if x < self.map_width and y < self.world.height*self.tile:
                    x, y = x // self.tile, y // self.tile
                    agents = [a for a in self.world.agents.values() if a.x == x and a.y == y]
                    if agents:
                        ids = sorted(a.id for a in agents)
                        self.selected = ids[(ids.index(self.selected)+1) % len(ids)] if self.selected in ids else ids[0]

    def advance(self, seconds):
        if self.saving:
            return
        if self.single_step and self.paused:
            self.world.step()
        self.single_step = False
        if not self.paused:
            self.accumulator = min(300.0, self.accumulator + min(seconds, 0.25) * self.speeds[self.speed_index])
            deadline = time.perf_counter() + 0.012
            while self.accumulator >= 1:
                self.world.step()
                self.accumulator -= 1
                if time.perf_counter() >= deadline:
                    break  # Keep backlog, but service controls between complete ticks.

    def draw(self):
        w, tile = self.world, self.tile
        self.screen.fill((19, 24, 29))
        for y, row in enumerate(w.cells):
            for x, c in enumerate(row):
                rect = pygame.Rect(x*tile, y*tile, tile-1, tile-1)
                pygame.draw.rect(self.screen, COLORS[c.terrain], rect)
                if c.food >= 10:
                    size = max(1, c.food * (tile-3) // 100)
                    pygame.draw.rect(self.screen, (107, 148, 69), (x*tile+1, y*tile+tile-4, size, 2))
        # Corpses first so living agents on a shared cell remain visible.
        ordered = sorted(w.agents.values(), key=lambda a: (a.alive, a.id))
        for a in ordered:
            center = (a.x*tile+tile//2, a.y*tile+tile//2)
            if not a.alive:
                pygame.draw.line(self.screen, (96, 87, 84), (center[0]-3, center[1]-3), (center[0]+3, center[1]+3))
            else:
                color = (133, 151, 179) if a.sleep_until > w.tick else (235, 203, 131)
                pygame.draw.circle(self.screen, color, center, max(2, tile//4))
            if a.id == self.selected:
                pygame.draw.circle(self.screen, (250, 250, 245), center, max(4, tile//2), 1)
        living = w.living()
        asleep = sum(a.sleep_until > w.tick for a in living)
        lines = ["GNOME FORTRESS", f"Seed {w.seed} | tick {w.tick}",
                 f"{'SAVING' if self.saving else 'PAUSED' if self.paused else 'RUNNING'} | {self.speeds[self.speed_index]} ticks / sec",
                 f"Living {len(living)} | asleep {asleep}",
                 f"Born {len(w.agents)} | dead {len(w.agents)-len(living)}",
                 f"Decision slots {sum(i is not None for i in w.slots)}/60", "",
                 "Space pause | +/- speed | . step", "Click gnome / Tab inspect | S save", "Esc quit and save", "",
                 "Food: green bars | water: blue", "Hazard: red | obstacle: gray", "Sleeping: blue | dead: cross", ""]
        a = w.agents.get(self.selected)
        if a:
            lines += [f"{a.name} | {'alive' if a.alive else a.death_cause}",
                      f"Age {a.age} | children {a.children} | {a.action}",
                      f"Health {a.health} | hunger {a.hunger}", f"Thirst {a.thirst} | fatigue {a.fatigue}",
                      f"Parents: {', '.join(map(str, a.parents)) or 'founder'}",
                      "Inherited traits: " + ", ".join(f"{k[:3]}={v}" for k, v in list(a.traits.items())[:3]),
                      "  " + ", ".join(f"{k[:3]}={v}" for k, v in list(a.traits.items())[3:]),
                      "Learned movement associations:"]
            lines += [f"  {k}: {v}" for k, v in sorted(a.learned.items()) if k.startswith("move:")]
            relations = sorted(a.relationships.items(), key=lambda p: (-p[1], p[0]))[:3]
            lines += ["Outgoing relationships: " + (", ".join(f"{i}={v}" for i, v in relations) or "none"),
                      "Recent episodes:"]
            lines += [f"  t{m.tick}: {m.action} {m.feature} {m.reward:+d}" for m in a.memories[-3:]]
        lines += ["", "Recent events:"]
        lines += [f"t{e.tick} {e.kind}: {e.actor}" for e in w.events[-3:]]
        for i, line in enumerate(lines):
            self.screen.blit(self.small.render(line, True, (216, 224, 224)), (self.map_width+12, 14+i*17))
        pygame.display.flip()


def run(world, checkpoint, save_callback, checkpoint_ticks=300, max_frames=None,
        stop_requested=lambda: False, rate=None, paused=False, stats_every=10):
    observer = Observer(world,rate,paused)
    clock = pygame.time.Clock()
    last_save = world.tick
    frames = 0
    worker = CheckpointWorker(save_callback)
    statistics = Statistics(stats_every)
    try:
        while observer.running and not stop_requested() and (max_frames is None or frames < max_frames):
            seconds = clock.tick(10 if observer.paused or worker.pending else 60)/1000
            was_saving = observer.saving
            events = pygame.event.get()
            observer.handle(events)
            if not observer.running:
                break
            completed = worker.pending and worker.future.done()
            if completed:
                checkpoint_notice(worker.poll())
                last_save = world.tick
                observer.saving = False
                seconds = 0  # Checkpoint wall time is not simulated catch-up time.
            observer.saving = worker.pending
            observer.advance(seconds)
            if not worker.pending and (observer.save_requested or world.tick-last_save >= checkpoint_ticks):
                worker.start(world,checkpoint)
                observer.saving = True
                observer.save_requested = False
            if (frames == 0 or events or completed or was_saving != observer.saving
                    or (not observer.paused and not worker.pending)):
                observer.draw()
            statistics.update(world,worker.pending,observer.paused)
            frames += 1
    finally:
        try:
            pygame.quit()
        finally:
            worker.close()
