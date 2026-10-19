# Observations and defects (baseline retained)

2026-10-19, before study execution:

- The observer's “Decision slots” is the number of assignments retained at the END
  of a tick. Sleeping/dead agents have already relinquished slots, so it cannot
  measure decisions actually executed that tick. This is a display/interpretation
  limitation, not an engine change request. The research harness measures both.
- Death causes are terminal-rule labels. A death with both hunger and thirst damage
  is labeled dehydration by the current rule. Do not interpret labels as mutually
  exclusive physiological contributions. Preserve the labels in the study data.
- Founder `born=0` is entry into the experiment, while initial age is 120–300.
  Lifespans must not equate founder death tick with biological age at death.

No rule fixes have been applied. Record additional reproducible problems here before
any implementation change.

Real-window observer check:

- Keyboard controls through OS-delivered X11 events passed, and visible frames were
  inspected. XSendEvent mouse coordinates did not select the intended cell. This
  could reflect SDL/XWayland synthetic-input handling; it is NOT established as a
  simulation/viewer defect. Physical mouse targeting remains unconfirmed. The
  original offscreen mouse test passes. No viewer code has been changed.
