# Phase 4B implementation findings before correction

The first focused run passed 27 tests and failed an over-strong control assertion:
individual and direct-transfer worlds cannot have identical complete agent state,
because B legitimately retains a warning in the direct condition. Compare full
individual versus masked core state (excluding hear episodes), and compare C's
state/RNG/cells across individual, direct and masked. Keep B's real difference.

A related observation: in a masked control C can subsequently enter the hazard;
its new firsthand proof then replaces the earlier masked receipt. Counting chains
from final current knowledge would undercount delivered chains. Preserve a bounded
copy of the proof input to each agent's latest movement and count delivery from
that pre-decision evidence. Do not change the movement outcome to retain a story.

Follow-up assertions required the same distinction: a masked `hear` episode is
expected to differ from no episode, while C's non-message state/RNG match. After
an interrupted relay C may legitimately acquire its own firsthand proof by entering
the hazard; the requirement is no social knowledge before that decision, not no
knowledge afterward. Tests now check those inputs and retain actual outcomes.

Measurement correction before finalization: the initial duplicate-storage stress
started after C moved, so the attempted repeats could be nonlocal. Repeat the
measurement after tick 2 while B and C are adjacent, and record the rejection
reason counts. The existing duplicate unit test already uses this valid placement;
this correction affects the measurement, not the channel or cohort outcomes.
