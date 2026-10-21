# G8A.1 implementation plan

Baseline: 2636861062eb8762c55335943379613ed457a5b1; main; clean on inspection. Protect the live checkpoint: use fresh in-memory worlds and temporary checkpoint paths only.

1. Replace placeholder art behind the existing pixel_art API. Produce eight real silhouette variants, sleep/walk states, archival portraits, five terrains, icons and journal frames. Cache native and scaled surfaces; keep alpha masks derived from displayed pixels.
2. Retain Camera and all input/target transforms. Keep crowd offsets, alpha-mask picking, repeated-click cycling and selected priority. Add read-only neighbor/provenance cache keys at terrain rendering only.
3. Reskin LivingObserver locally. Preserve all original research and legacy viewer modules, Saveguard runner and storage. Use actual records for historical details and event icons. No persistent UI state or new events.
4. Run focused existing and new tests first. Test all supported sizes, masks, state/RNG invariance and controls. Then run the full fast suite with long research campaign excluded as before.
5. Generate actual running-view screenshots and one unified asset sheet. Use natural worlds for events and clearly identify scripted environmental actions. Profile young and generated 26,000-tick worlds at four sizes, cache footprints, dense rendering and background saving. Compare against baseline using an isolated checkout/source snapshot, never the owner's game.
6. Audit protected sources and historical evidence, document executed checks and limitations, commit and push without force. Stop for owner review.

Risks: more detailed sprites may disappear at whole-world zoom; close inspection is essential. Larger native art must retain old displayed proportions and exact alpha picking. Neighborhood work must be capped at visible tiles; history lookup must use existing incremental indexes. Cached texture detail may cost more at 4K. The existing detached-snapshot capture hitch is outside this art pass.
