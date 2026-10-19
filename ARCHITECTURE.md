# Architecture and experiment boundaries

## Explicit state

`model.py` defines ordinary dataclasses for cells, agents, episodes and events.
`engine.py` owns the world, all rule execution, and one private `random.Random(seed)`.
`storage.py` translates this state into queryable SQLite tables. `viewer.py` observes
and advances the engine; the engine imports neither Pygame nor SQLite. The command
line provides headless execution and checkpoint ownership.

All biological and decision quantities are integers. Simulation time is an integer
world tick, independent of frame rate and real elapsed time. Agent IDs are monotonic,
never reused, and distinct from names. Dead agents, ancestry and significant events
remain present permanently. Founders begin at a seeded age between 120 and 300 ticks;
offspring begin at age zero. Identities are never respawned or resurrected.

## Tick ordering and 60-slot waterfall

Each tick executes, in order:

1. Increment world time; regenerate food every tenth tick in row-major order.
2. Advance biology for **every living agent** in ascending identity order: age,
   cooldown, hunger, thirst, fatigue, healing, need deaths and old age. Sleep reduces
   fatigue, but does not stop aging or hunger/thirst. Urgent needs can wake an agent.
3. Gather living, awake agents in ascending ID order. Rotate after the previous
   cursor identity, take at most 60, and assign them once each to the 60 decision slots.
4. Run those decisions in slot order. Decisions are sequential: later agents see
   earlier agents' actions. Newborns become eligible at the next tick. A parent can
   receive an interaction while another agent acts; it still gets at most one own
   decision. This ordering is a deliberate model choice.
5. Clear slots relinquished by sleeping or death. They are refilled at the next
   world tick. Persistent identity and memory do not belong to a scheduling slot.

This is a rotating waterfall, not 60 permanently assigned founders. With more than
60 eligible agents, others wait in ID rotation. Births, deaths and sleepers cannot
reset the cursor to the beginning. At most 60 decisions execute per tick; no agent
receives extra biological time from gaining a slot. Newborn biology begins on the
following tick. With no living population the world continues ticking; extinction
never triggers reseeding.

## Decisions, inheritance and learning

An agent sees cells within a Manhattan radius of `3 + vision // 25` (3–7 cells),
including through obstacles. Peer interactions require distance at most one.
Movement is one orthogonal cell; rock and water are impassable. Drinking is possible
next to water. Decisions have an explicit rule priority:

1. Drink at thirst ≥30 if water is accessible.
2. Eat local food at hunger ≥30.
3. Sleep for 12 ticks when fatigued, if needs permit.
4. Attempt reproduction with an eligible adjacent peer.
5. Attempt a social interaction when needs permit.
6. Move using locally observed resources, exploration, social proximity and learned
   terrain consequences; wait if surrounded.

Movement scores use resource distance improvement weighted by needs, an inherited
caution penalty for hazards, a curiosity term, a visit penalty, social proximity,
and the learned movement association for the destination terrain. Best-score ties
use the private RNG. Curiosity supplies a larger bonus for previously unvisited cells; revisited cells
receive a visit-count penalty. A controlled test verifies that changing only
curiosity can shift a choice between a visited food cell and an unvisited cell.

The six inherited trait integers are curiosity, caution, sociability, fertility,
stamina and vision. Two eligible mature gnomes can reproduce irrespective of sex;
traits use the parents' integer mean plus uniform variation from −10 to +10,
clamped to 0–100. Maturity is age 180; reproduction requires health ≥70, low needs,
zero cooldown, an adjacent eligible peer and a seeded fertility probability.
Both parents pay hunger/fatigue costs and receive a 240-tick cooldown. No carrying
capacity, population target or generational era is imposed. Stamina sets a finite
lifespan of `1800 + stamina * 12` ticks.

Each experienced eating, drinking, movement, reproduction or social consequence
creates an episode containing tick, action, position, feature and programmed reward.
Only the latest 64 episodes per agent are retained; the association table and visit
counts persist beyond episode eviction. Sleeping never clears them.

The association update is explicit:

```
association[action:feature] = clamp((3 * old + reward) // 4, -100, 100)
```

Only **movement** associations affect decision scores in this milestone. Entering a
hazard causes a seeded 12–30 health loss and reward `−3 * damage`. Ordinary movement
has reward zero. This is a simple learned aversion generalized to the `hazard`
feature; inherited caution is a separate fixed tendency. Eating/drinking/social and
reproductive associations are recorded by the same mechanism but currently have no
decision effect. The code does not pretend those unused values demonstrate learning.
The memory test removes only associations in an otherwise identical paired state
and measures the change in hazard choices.

Directional relationship values increase after programmed social encounters and
reproduction. Sender and recipient increments differ according to traits. These
are elementary interaction records; they do not establish friendship, language,
cooperation or social institutions. Values do not currently affect mate choice or
movement. Nothing in the model specifies civilizations, governments, religions,
languages, technologies or ages.

## Persistence and reproducibility

SQLite stores world metadata (including full RNG state, scheduler cursor and slots),
terrain and food, agent state, ordered ancestry, recent memories, directional
relationships and the ordered event log. Learned tables and visit counts are in
agent JSON state. SQL columns expose identity, liveness, birth and death directly.
A checkpoint commits a complete logical snapshot in one SQLite transaction.
Unchanged, content-checked agent rows are reused; new events append only when the
complete prior prefix matches. Untrusted targets and divergent histories are fully
rewritten. Dead records are checked too, so external changes cannot be silently
omitted. New checkpoints retain schema-1 tables, with an integrity extension marked
by SQLite user_version=2. Original user_version=0 archives remain readable.

A failed save rolls back to the prior checkpoint. Loading pins one read transaction
and verifies record sequences and new-format logical checksums. Header checks run
before materializing dimensions. A hot rollback journal permits existing-file
read/write recovery; ordinary loading is read-only and never creates missing files.
The old reader can inspect new table contents; the old writer must not strip the
new integrity metadata. Simulation state format remains version 1.

Examples using the optional system `sqlite3` command:

```sql
SELECT alive, count(*) FROM agents GROUP BY alive;
SELECT kind, count(*) FROM events GROUP BY kind;
SELECT child, parent FROM ancestry ORDER BY child, position;
SELECT tick, action, feature, reward FROM memories WHERE agent=1 ORDER BY sequence;
SELECT source, target, value FROM relationships ORDER BY value DESC LIMIT 10;
```

The state digest includes world cells, all identities, recent memories, learned
values, visits, relationships, ancestry, events, slots and RNG state. Equal digests
at the same tick compare the entire current experiment state. SQL row order, display
speed, process hash seed and wall time cannot affect simulation decisions. SIGINT
and SIGTERM set a stop flag; a checkpoint follows a completed tick, including when
the signal arrives during an update. SIGKILL can recover only the last checkpoint.

The reproducibility claim is tested on the recorded Python version and rule version.
Changing code, constants or random-library implementations defines a different
experiment; cross-version equivalence is not guaranteed. Founders have distinct IDs
and names; their trait vectors are independently sampled, not guaranteed unique.

## Limitations and unattended operation

- Food replenishment, water supply, initial conditions and reproduction costs are
  deliberately artificial. The world does not conserve biomass or energy.
- Local Manhattan heuristics have no path planning; agents can become stuck behind
  obstacles or die while resources exist elsewhere. The nursery guarantees some
  resources, not reachability for every founder. No extinction prevention is used.
- Perception sees through walls. No inventories, construction, combat, tasks,
  narrative generator, neural models or hidden social systems exist.
- All recent episodes are bounded to 64 per identity; historical episodes beyond that
  are forgotten. Significant events and dead identities are never pruned. Visit
  memory is bounded by world cell count per agent. Archive size grows with births
  and events, so this is a prolonged-run prototype, not a promise of bounded storage
  for years. Integrity verification still reads and hashes complete retained
  histories; checkpoints are faster but not constant-time.
- A derived insertion-ordered index contains living agent references. Proximity
  queries read current coordinates directly; birth/death and loading maintain the
  index. No duplicated position cache or sensory-rule change is introduced. The
  60-decision budget limits decisions, not archive size. Explicit structural
  interventions must use spawn/kill or reload state, so the index stays valid.
- The observer can show overlapping dots and corpse crosses on the same tile.
  The panel and SQLite records provide exact population and identity accounting.
- No editable world interventions are available. Pause, speed and inspection only
  affect observation. Adding interventions later must include a tick-stamped log.

## Research lineage

The Phase 0 proposal to test memory survival was carried out in Phase 2 using
20 matched seed pairs at 20,000 ticks. Its findings and limits remain preserved
in research/phase2/REPORT.md. Phase 3 changes execution and persistence only.
The next research objective is whether useful information can pass between
individuals and survive across generations. That work is not implemented here.

## Phase 3 operational ownership

The observer freezes stepping at a complete tick while one writer thread saves.
Rendering, inspection, pause, speed and quit events continue; the writer and main
thread never mutate biological state concurrently. Single-step requests during a
checkpoint wait until writing finishes. Shutdown joins an outstanding write before
the final checkpoint. Save wall time creates no simulated catch-up debt.

Running frames limit catch-up work to complete ticks within a short time budget,
retaining at most 300 ticks of pending pacing work. Speed changes clear that
wall-clock debt; logical ticks are always executed completely and sequentially. Paused loops sleep at 10 Hz and avoid repeated draws.
Headless execution supports finite runs or --forever, optional --rate pacing,
and periodic stderr statistics. None of these clocks or derived caches enters
serialized biological state or the RNG. See research/phase3/REPORT.md for measured
performance and the frozen Phase 2 comparison. The next research objective is
transmission of useful information across individuals and generations; none is
implemented in this engineering phase.
