# G4 implementation boundary

Accepted G3 inspected on clean main at 40eeac5cb8893f02d32e456b4a778badf3cc998f.
Reviewed god_viewer, game_presentation, life_presentation, game, game_storage,
G3 review/results and existing viewer tests. WorldPresentation already supplies
incremental events and current ledger overlap; Life supplies actual life status.
No core defect or save migration is needed for this feature.

Implement one ephemeral Advisor with explicit topic/choice conditionals and a
right-panel overlay. Keep the world, global feed, Watch and world statistics
visible. Button/A toggles, digits select, 0 backs/closes; Escape retains exit.
Sample facts on choice, not per frame. Navigate to existing views, preserving
identity and Watch. Use latest five indexed deaths, not a second browser/archive.
No dependencies, RNG, events, world writes or persistent advisor state.

Verify every branch, invalid input, missing/dead/sleeping identities, current and
historical intervention accounting, controls/navigation, no mutation/RNG draws,
render cadence and existing saves. Run focused then fast tests, actual X11
scripted controls/capture, and source/preservation compatibility checks. No
research campaign, mode implementation, powers, predators or G5.
