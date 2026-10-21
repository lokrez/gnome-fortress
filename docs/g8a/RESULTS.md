# G8A — First Contact

Implemented and verified as a presentation-only extension to accepted Saveguard
`58bfbd424214aa4fad8abe65f444cdd3032b2cd9`. No G8B or new simulation mechanics.
Final delivered commit SHA is printed in the handoff; `git log -1 --format=%H`
identifies the delivered checkout. [Plan](PLAN.md), [controls](CONTROLS.md),
[performance](PERFORMANCE.md).

## What changed

The normal terrain launcher now opens LivingObserver: a larger camera viewport,
original pixel-art gnomes and textured terrain, native-size text, a contextual
individual card, compact World Happenings and progressive detail/history tabs.
The only modified pre-existing production file is terrain_viewer.py's viewer
entrypoint. The original observer class remains intact for reference; the new
observer reuses its presentation indexes, factual helpers, Advisor and exact
existing Saveguard run loop/worker.

Camera conversions govern every terrain tile, sprite, pick, footprint and power
preview. Wheel zoom is anchored to the pointer (or viewport center during follow).
Arrows/middle drag pan; Home fits; Center moves once; C follows a living identity.
World edges clamp centering, so a target near an edge need not occupy the exact
viewport center. Sleep remains followable; death stops tracking without switching
selection or erasing Watch/history. On opening an existing world, the initial
selection is its first living identity, if one exists, rather than a dead founder.

Sprites use identity-derived cosmetic hat/clothing/beard variants and nearest-neighbor
scaling. They do not encode biological sex, occupation, traits or intelligence.
Feet animate from recorded movement/tick state; sleeping reclines; pause has no
travel interpolation. Crowds have visual-only offsets, bounded visible sprites,
real occupancy counts, selected draw priority and repeated-click occupant cycling.
Actual displayed alpha masks, selected labels and outlines determine hits.

The Overview card shows actual status, latest recorded action, appropriately
scaled needs, age, current/final location and family access. Details exposes real
traits, associations, episodes and numeric relationships; Life and Family reuse
one disposable selected-person index. Gnomes' intentions are never inferred.

Terrain has recognizable grass, trees, stones, blue water and fractured hazard.
A top legend/hover label names it. Optional food bars show actual stores. Active
Rain/Drought, queued outlines, eligibility previews and historical divine badges
remain distinct; Land and Powers retain exact transition/resource accounting.
The same tile transform aims all five unchanged divine powers.

World Happenings uses the existing incremental objective index. Birth/death/hazard
and divine events are plainly labelled, timestamped and clickable. Event locations
are used only when recorded; a missing location explicitly falls back to current
or final stored position. No paths, motives, friendships or invented histories are
created. The Advisor remains the same scripted conditional system; factual replies
are labelled as sampled when a topic is selected.

## Input safety and layout

HUD -> Advisor -> explicit power -> explicit Land -> visible gnome -> underlying
tile. O/right-click cancels targeting. Sidebar navigation and Advisor disarm powers;
casting keeps the explicitly selected power armed. Arrows replace the old secondary
speed aliases; +/- remain speed controls. Esc still saves/exits, never closes a menu.
The inspector/feed can collapse, resize is supported from 800×600, and native
fonts/panels grow at large desktop dimensions. Terrain/sprites are culled to the
viewport. No image asset service, dependency or network access is needed.

A targeted interaction review found and fixed an invisible-modal risk: collapsing
the inspector while Advisor was open could hide it without releasing map input.
Closing the inspector now closes that dialogue; a regression test covers it.
Missing record messages, crowd labels and clamped camera edge behavior were also
checked. No defect in the underlying biological rules was found or changed.

## Executed verification

- [Focused tests](evidence/targeted-tests.txt): **35 passed in 6.47s**.
- [Full fast suite](evidence/fast-tests.txt): **261 passed in 141.61s (0:02:21)**.

Coverage includes transform round trips, bounds, zoom anchors, all five targeted
powers after camera movement, edge targeting, modal/HUD priorities, exact crowded
sprite picks/cycling, ID appearance persistence, awake/sleeping/dead states, missing
records, family/event navigation, numeric need scales, event-index scan counts,
UI read-only/RNG preservation, fixed-tick rendering-cadence equality, actual launcher
save/load and new UI activity during a detached checkpoint. Existing Saveguard
crash/ownership/hot-journal, legacy readers and pinned research reference tests
also passed. No 20,000-tick research test or historical archive campaign was rerun.
A generated 26,000-tick graphics fixture is separate from those campaigns.

[Preservation audit](evidence/preservation.json): **664 baseline tracked files
unchanged**, except the explicitly excluded README and terrain entrypoint. The
old TerrainObserver class is AST-identical. Engine/model/learning/reproduction,
terrain/powers/events, all Saveguard files, storage formats, game-mode contract,
G1–G7 documentation and historical Git tags are unchanged. Ignored datasets were
not rehashed, rewritten or used for development. Live owner PID 402014 and its
checkpoint were not launched, loaded, terminated or replaced.

## Running-build evidence

All captures are actual Pygame output, using natural seed-1 simulation updates.
The only environmental intervention is the documented UI Rupture request at tick
300. Screenshots do not contain synthetic gnome activities. Metadata and frame/
follow traces: [captures.json](evidence/captures.json). Scripted SDL-dummy operation
is not a human playtest or a claim the interface is enjoyable to a novice yet.

| Capture | Demonstration |
|---|---|
| [New world](captures/00-new-world.png) | 60 original founders, map art, legend and compact hierarchy |
| [Zoomed gnome](captures/01-zoomed-gnome.png) | Recognizable silhouette and stable cosmetic identity |
| [Individual card](captures/02-individual-card.png) | Same real tick-120 view, emphasizing actual action/needs/family access |
| [Camera follow](captures/03-camera-follow.png) | Living follow enabled; the 30-tick trace contains actual movement |
| [World Happenings](captures/04-world-happenings.png) | Natural objective injuries/births with ticks |
| [Targeting](captures/05-transformed-target-preview.png) | Camera moved/zoomed; preview and accepted Rupture coordinates exactly match |
| [Land history](captures/06-recorded-land-history.png) | First actual changed cell; transition data from the authoritative record |
| [Autosave](captures/07-autosave-running.png) | RUNNING and SAVING together; older snapshot and newer live ticks distinguished |
| [800×600](captures/08-small-window.png) | Inspector collapsed; controls/feed fit without overlapping the map |
| [3840×2160](captures/09-4k-window.png) | Real high-resolution surface with native text and larger world scale |
| [Life](captures/10-personal-history.png) | Actual personal objective timeline of the first retained descendant |
| [Direct family](captures/11-direct-family.png) | Real parent/child record links and status |

The follow trace records **16 actual position changes**. The controlled 0.5-second save delay kept the world running from tick **600 to 611**; snapshot tick **600** was drained, then the latest world committed/reloaded exactly. No frame-rate-based game input or UI-only state enters checkpoints.

## Performance and remaining limits

New drawing medians were about 6.5–7.3 ms at 1280×720 in these fixtures. It costs
more than old flat rendering on young worlds, while the 26,000-tick view improved
from 8.60 to 7.33 ms median by avoiding retained-deceased drawing. Full distributions,
zoom/follow/population costs and append-only index measurements are in the
[performance report](PERFORMANCE.md). These are not a blanket FPS guarantee.

Saveguard's remaining large-history capture hitch is unchanged: previously measured
about 156 ms median / 226 ms worst at 10,000 ticks. G8A does not claim to eliminate
it. World/event history still grows; UI caches and visible per-tile bodies are
bounded, not the scientific history. Very dense tiles require cycling, and ordinary
nearby overlapping sprites can still require zoom to inspect comfortably.

The camera is tile-based without travel interpolation. No full ancestry tree,
fictional dialogue, settlements or new gameplay systems were added. A 30-second
novice check and a longer real-desktop/4K playtest remain human follow-up, especially
for visual density, font size, crowd selection and long-world autosave latency.

## Launch / reproduction

Save and exit the old running process with Esc; wait for the terminal prompt.

```bash
cd ~/gnome-fortress
git pull --ff-only
.venv/bin/python -m gnome_fortress.god_world
```

The same gameplay file resumes. For isolated development/evidence:

```bash
.venv/bin/python -m pytest -q tests/test_g8a.py tests/test_terrain_checkpoint.py tests/test_game_session.py
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
.venv/bin/python -m research.g8a_evidence --out /tmp/g8a-captures
.venv/bin/python -m research.g8a_evidence --bench --out /tmp/g8a-performance
```

The research/legacy launch commands and checkpoint readers remain available.
Stop at G8A. No G8B, LLM integration, progression, new powers or social mechanics.
