# G8A.1 — The Living Folklore

Accepted parent: `2636861062eb8762c55335943379613ed457a5b1`. Original art source is `gnome_fortress/pixel_art.py`; no pixels were cut from the owner's reference. The supplied JPG and the chosen palette, dimensions, lighting and replacement API are documented in [ART_BIBLE.md](ART_BIBLE.md).

## Delivered

Eight distinct crooked-hat silhouettes with noses, ragged beards, tiny coats/boots, worn stitching and restrained moss patches. Awake/walking/reclining appearances and a separate archival death portrait. Five terrain families with fixed coordinate grain, irregular foliage/stone shapes, dark water and exposed fissures. Neighbor-aware edge marks and genuine last-transition treatments preserve Rupture, Rewild and Wellspring provenance. H still toggles historical presentation.

The existing layout is reskinned with paper, copper/ink tabs, botanical margins and custom power/event glyphs. The specimen card uses a larger portrait and the same actual status/actions/needs/family data. Advisor remains the original scripted conditional dialogue. No new factual claims, characters, behavior, events, save fields or dependencies.

## Run

```bash
cd ~/gnome-fortress && .venv/bin/python -m gnome_fortress.god_world
```

All G8A controls remain: wheel zoom, arrows/middle-drag pan, C camera follow, W Life Watch, O/right-click disarm, R/D/E/F/P powers, I inspector, F1/F2/F3 views, T Land, H historical marks, B food, V happenings, A Advisor, Space pause, S save, Esc save and exit. Wait for the terminal prompt before relaunching. This command resumes the existing prototype save under unchanged ownership protection; it does not create a second world.

## Executed evidence

See [targeted tests](evidence/targeted-tests.txt), [full fast tests](evidence/fast-tests.txt), [performance](PERFORMANCE.md), [preservation audit](evidence/preservation.json) and [capture metadata](evidence/captures.json). Executed results: **38 targeted tests passed (4.67 s)** and **273 full fast-suite tests passed (147.57 s)**. The final fast run includes all art cleanup and the constrained-window fix. Earlier intermediate green logs are retained separately. The known long research run remains excluded using the established fast-suite command. No historical archive campaign or survival experiment was launched.

The tests cover stable appearance across cache clearing/save-load/cadence, eight distinct alpha silhouettes, scaling/mask bounds, all five power targets, exact composed-art equivalence, crowds, sleeping/dead records, recorded provenance, truthful glyph fallback, four window sizes, state/RNG invariance, Saveguard integration and the existing reference/save regressions.

Confirmed related defect: on the real desktop the window manager constrained a requested 3840×2160 decorated window to 3840×2060. G8A used requested dimensions for initial/resize layout, which could put the bottom UI outside the actual surface. LivingObserver now lays out the actual returned surface. A constrained-window regression covers initialization and resize. Camera math is unchanged. The 4K evidence uses a temporary borderless desktop window to obtain an actual 3840×2160 surface; ordinary gameplay remains resizable/windowed.

## Running-build evidence

These are actual Pygame/X11 captures, not generated mockups. The sandbox initially lacked display access; the bounded desktop checks then ran successfully with desktop permission. No human playtest or owner art approval is claimed.

- [Fresh world](captures/01-new-world.png)
- [Several natural occupants](captures/02-natural-gnomes.png)
- [Close-up](captures/03-close-gnome.png) and [field-journal card](captures/04-field-journal-card.png)
- [Living camera follow](captures/05-camera-follow.png)
- [Scripted Advisor](captures/06-advisor.png)
- [Objective happenings](captures/07-world-happenings.png)
- [Targeting](captures/08-divine-targeting.png)
- [Ruptured land](captures/09-ruptured-land.png) and [subsequently rewilded history](captures/10-rewilded-land-history.png)
- [Five terrain types](captures/11-five-terrain-types.png)
- [800×600](captures/12-800x600.png), [1920×1080](captures/13-1920x1080.png), [full 4K](captures/14-4k-viewport.png)
- [Detached save while running](captures/15-background-save.png)
- [Three-frame real launcher check](captures/16-desktop-launch.png)
- [Unified actual asset sheet](art-sheet.png)

Seed 1 is advanced normally to tick 300; the natural most occupied tile is selected for the crowd view. Follow advances 20 more ordinary ticks. For readable targeting evidence, the first interior forest tile with a three-tile map margin is selected before examining outcomes; Rupture and Rewild are requested at successive ordinary boundaries. This replaces an initial edge-of-map capture target solely to keep the preview visible. No agents are relocated, injured, killed, born or given fake actions for screenshots. The asset sheet is an asset comparison, not a simulation scene. The dense benchmark/test alone relocates 60 founders as an explicitly synthetic presentation fixture.

## Preservation and limits

Only the LivingObserver presentation and art module change existing Python source. Engine/model, camera transforms, game mechanics, checkpoint readers/writers, ownership, recovery and Saveguard are unchanged. Earlier research/gameplay evidence and tags are preserved. The player's live checkpoint was never opened by the development/evidence commands. Temporary files and generated worlds are separate.

This is original procedural pixel artwork, not the painted complexity of the much larger concept image. Details are intentionally lost at whole-map zoom; close view and the portrait expose them. Terrain remains tile-based; boundary treatment softens edges without pretending the map is continuous or adding bridges/elevation. Sleep is a restrained reclining pose; walking changes the existing recorded-action foot pose. No new activity or idle psychology is animated.

The warm journal keeps native Pygame typography for predictable legibility. Bounded caches have a memory cost; cold zooms can take longer than steady drawing. Software-render benchmarks are not laptop/4K compositor FPS promises. The preexisting large-history snapshot hitch remains visible and is documented separately. Art quality and usability await the owner's review. G8B was not started.

## Reproduce

```bash
.venv/bin/python -m pytest -q tests/test_g8a.py tests/test_g8a1.py
.venv/bin/python -m pytest -q --ignore=tests/test_long_run.py
SDL_VIDEODRIVER=x11 .venv/bin/python -m research.g8a1_evidence --out /tmp/g8a1-captures
.venv/bin/python -m research.g8a1_evidence --bench --out /tmp/g8a1-benchmark
```

The benchmark reads the accepted G8A art/view source from Git into disposable modules for comparison, never checks it out over this tree, and creates one bounded 26,000-tick fixture. Baseline history must be present. Capture/benchmark output defaults to this milestone directory; use `--out` to preserve the committed evidence when reproducing.
