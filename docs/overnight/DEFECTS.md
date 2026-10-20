# Confirmed defects and fixture corrections

No defect in the preserved biological rules, research reference or legacy save
format was identified or modified in this campaign.

1. **New G7 Land button blocked map targeting.** Initial 61-test integration
   reported 2 failures. Documented in WORKLOG before repair; kept the failing
   assertions. Land moved into a fourth inspection tab; terrain Advisor button
   moved below the map into the event-header margin. The map is fully targetable.
   Targeted rerun: 61 passed. Original failing log retained under docs/g7.
2. **New G5 storage API accepted the wrong world class.** Directly reproduced
   create_game(GameWorld(), unused_g5_path): save returned success, G5 reload
   rejected its legacy payload. Fixed before delivery: both new-file creation
   and update require TerrainWorld before any writes. Tests verify missing files
   stay missing and existing files remain byte-identical. New record/version
   integers and transition metadata also reject boolean impostors; optimized
   Python cannot silently disable inherited assertions. No format/physics change.
3. **New G7 inspection mode survived Watch navigation.** Reproduced T→W leaving
   Life open with tile targeting enabled. Clear the ephemeral terrain targeting
   flag on W, Tab and right-click, as on F1–F3. Exact world/RNG and navigation
   assertions verify the fix; no recorded-world field changes.
4. **Test fixture setup, not a software defect.** Initial extra autosave test
   started at tick 1, which initialized last_save to tick 1 and never made a save
   overdue. Corrected by stepping once after loop initialization; retained exact
   two-attempt, no-repeat, explicit-retry and final-state assertions. Initial
   failure log retained; operational rerun passed all 4 checks.

No assertions were loosened to hide failures. Final reports identify the executed
regression runs and source audit. These corrections are part of the final safety
verification commit, separately from the four feature commits.
