# First Contact — playing the existing world

Launch/resume the terrain game as before:

```bash
cd ~/gnome-fortress
.venv/bin/python -m gnome_fortress.god_world
```

Exit the old running version with **Esc**, and wait for the terminal prompt before
updating/relaunching. Do not use Ctrl+Z as an exit. Saveguard ownership is unchanged.
For a separate fresh world, use `--new --db /path/to/unused.g5.sqlite`.

## Your first 30 seconds

1. The pointed hats are living gnomes. Trees, stone shapes, water and cracked
   hazardous ground have distinct textures; the top legend and hover labels name them.
2. Wheel over the map to zoom; arrows pan 64 screen pixels per press. Middle-drag
   also pans. **Home** fits the whole map. Zoom is anchored at the pointer in free
   camera; while following, it is anchored at the viewport center.
3. Click a gnome's body or selected ID label to inspect it. Its card shows the
   latest recorded action and actual needs. Repeated clicks in a crowd cycle its
   living occupants. The count is people on one tile; little offsets are cosmetic.
4. **C** or Follow toggles the selected living individual’s camera follow. Center
   moves the camera once. Pan stops follow while retaining identity. Sleeping is
   still living. Death stops live tracking and preserves the final stored record.
5. World Happenings shows actual births, deaths, injuries and divine events. Click
   a row for Life or an intervention target. **History** expands it; **V** cycles
   compact/expanded/hidden. Wheel there or PgUp/PgDn browses; End returns to latest.
6. Choose a named power or its key, inspect its exact tile preview, then click the
   map to request it. **O** or right-click cancels. An armed power has a highlighted
   toolbar button and explicit footer notice. It stays armed after casting until
   cancelled. Opening a sidebar inspection tab or Advisor disarms it.

## Controls

| Input | Effect |
|---|---|
| Wheel over map | Zoom, without moving world coordinates |
| Arrows / middle drag | Pan; stop camera follow |
| Home / Center button | Fit world / center selected individual |
| C | Toggle living camera follow |
| W | Toggle existing Life Watch (separate from camera follow) |
| O / right-click | Observe; cancel power and Land targeting |
| R / D | Arm Rain / Drought |
| E / F / P | Arm Rupture / Rewild / Wellspring |
| T | Explicit Land inspection; map clicks select terrain instead of people |
| H | Toggle historical divine footprint badges |
| B / Food button | Toggle real food bars on producing terrain |
| I / Inspect button | Show/hide contextual inspector |
| F1 / F2 / F3 | Overview / intervention records / Life |
| Family / Details / World tabs | Direct relatives / actual traits and learning / statistics |
| Wheel over inspector, [ / ] | Page its history, family, powers or details |
| L | Latest personal/Land history page |
| A | Scripted Advisor; number keys or buttons choose responses |
| Tab | Cycle retained identities, including deceased records |
| Space / . | Pause/resume / one complete tick while paused |
| + / - | Simulation speed (arrows are now camera controls) |
| S / Esc | Manual save / save and exit; final save may wait |

UI controls take precedence over the map. Advisor blocks map clicks while open.
Then map click priority is explicit power -> explicit Land -> displayed gnome ->
underlying tile. Camera zoom/pan and inspector changes never request a checkpoint.
A ledger tab does not itself arm a power. Small windows start with the inspector
collapsed; clicking a gnome opens it, and I hides it again. Resize is supported
from 800×600 upward; 1280×720 is the principal compact desktop layout.

## Reading the facts

- An action is the **latest recorded decision**, not an ongoing thought or intent.
- Health has maximum 100 and may finish below zero. Hunger/thirst use 0–150;
  fatigue uses 0–130. Higher needs are not equivalent to lower health. Biology
  applies damage above hunger/thirst 100; fatigue alone is not a diagnosis.
- Founders were initialized with existing age. Birth tick and recorded age need
  not differ by the current tick for a founder.
- Family is recorded parentage, not marriage or affection. Details exposes numeric
  outgoing relationship values without inventing social roles.
- Sleeping gnomes recline and have a z; their position is still one real tile.
  Hat/clothing/beard variation is cosmetic, derived from ID, not personality/sex/job.
- A deceased individual has a final-location marker, never a live position or follow.
  An event without coordinates explicitly falls back to current/final stored location;
  the game does not reconstruct unrecorded paths.
- Rain/Drought borders show current effects. Q outlines are queued requests.
  Preview crosses indicate currently ineligible cells; earlier queued actions may
  change eligibility. Bright tiles are eligible now, not a guaranteed future result.
- Corner badges mark ordered divine terrain history: red Rupture, green Rewild,
  blue Wellspring. A tile restored to its original terrain still retains its history.
  Land shows actual transitions and food. Powers shows real resource ledgers;
  regeneration differences do not establish population benefits.
- SAVING alongside RUNNING means a detached older-tick snapshot is being written.
  UNSAVED persists after failure; S explicitly retries. Success does not resume a
  safety-paused world automatically. Save formats and recovery rules are unchanged.

The original research and legacy G1 launchers remain available. G8A is the terrain
launcher's new presentation, not a new game mode, biological system or AI integration.
