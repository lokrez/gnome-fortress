# G8A — First Contact implementation plan

Preflight: clean main at accepted `58bfbd424214aa4fad8abe65f444cdd3032b2cd9`.
Host inspection found existing player session 402014 and writer 402234. Neither
will be launched, stopped, loaded or used for development. All fixtures are generated.
No repository-specific AGENTS.md applies. No simulation/save changes are planned.

## Existing renderer and input review

`viewer.Observer` initializes a fixed integer tile size; its map starts at (0,0).
`GodObserver` reinitializes a narrow full-map viewport with a 470px right panel and
an event area below the map. `TerrainObserver` adds two power rows and land tools.
`map_target` divides raw screen coordinates by tile size; marker placement, regions,
footprints and base click handling also multiply raw world coordinates. Therefore
changing tile size alone is not a camera: every map path needs the same transform.
Input currently goes Advisor -> terrain extra_input -> God controls -> base observer.
Map selection in the base scans retained agents (including dead), cycles tile IDs.
Arrow up/down are secondary speed aliases; +/- remain the primary speed controls.
World/Land event indexes are incremental; LifeHistory caches one selected identity.
Terrain checkpoint capture, process ownership and run-loop scheduling are separate.

## Architecture

- Keep original research Observer, G1 GodObserver and G7 TerrainObserver available
  unchanged as reference interfaces. Add a new terrain gameplay observer and route
  the existing terrain launcher's viewer entry point to it. Reuse the exact current
  Saveguard run loop and worker; no second runner, storage format or game world.
- Add a presentation-only camera with explicit tile/screen conversion, visible
  bounds, clamping, cursor-anchored zoom and selected-identity follow. All map art,
  picks, footprints, regions and previews use this transform. No interpolation.
- Add original procedural pixel surfaces: cached five-terrain tile textures and
  identity-derived hats/clothes/face decorations, nearest-neighbor scaled. No
  simulation RNG, network assets, saved cosmetics or inferred roles/sex.
- Render living agents only, with bounded per-tile visual offsets and selected
  draw priority; indicate crowded cells and allow repeated-click occupant cycling.
  Sprite alpha masks use exactly the displayed rectangles for picking. Deceased
  selections get a final-location marker; they are never live follow targets.
- Large map under compact status/power bars; compact collapsible happenings below
  the viewport; contextual right inspector with overview/details/Life/family/Land/
  ledger/stats. Responsive size and inspector collapse rather than overlapping UI.
  Font text is rendered at native size, never stretched with the map.
- Draw only visible tiles and sprites. Cache art and text with bounded LRU sizes.
  Reuse existing append-only event/terrain indexes; only one personal history cache.

## Input contract

Esc always saves/exits; Space/pacing/S retain their meanings. Explicit toolbar
arming or R/D/E/F/P selects power; O/right-click disarms and leaves Land targeting.
Advisor captures its panel/number choices and blocks map casting until closed.
After HUD handling: power targeting -> explicit Land inspection -> displayed sprite
selection -> underlying tile inspection. No HUD click falls through into the map.
Wheel on map zooms; wheel on histories scrolls. Arrows pan (replace old secondary
speed aliases; +/- retain speed). C toggles live follow; W retains Life Watch;
Center button centers without follow, Home fits the world. Manual pan stops follow
without changing identity. Selecting another individual stops the old follow.

## Truth and compatibility

Card uses actual action codes, sleeping/death state, family and need ranges:
health maximum 100 (can finish negative), hunger/thirst cap 150, fatigue cap 130.
Labels say latest recorded decision, not continuous intent. No imaginary thoughts.
Notifications use existing records. Missing event coordinates are explicitly
unavailable; current/final stored locations are labelled as fallback, never paths.
God powers still create normal requests at the existing tick boundary.

## Risks, gates and evidence

Coordinate errors are the primary blocker: test round trips, edges, pan/zoom and
all power previews/clicks. Test crowded alpha-mask picks, cycling, sleep/death follow,
small windows, modal precedence, family/event navigation, read-only world/RNG and
fixed-tick cadence equality. Execute Saveguard and full fast regressions (exclude
known long-run campaign). Compare old/new drawing on bounded fresh/mature/10,000-tick
fixtures; report capture hitch separately. Capture actual Pygame surfaces and a
scripted pending-save run. SDL-dummy checks are operational, not a human playtest.
Audit protected sources/data/tags against the accepted baseline, commit/push G8A,
and stop. G8B/social systems/LLMs remain out of scope.
