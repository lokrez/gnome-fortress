# G1 presentation deficiencies and G2 observations

Documented before changing the affected presentation behavior:

- G1 request notifications are historical strings and do not show current lifecycle.
  G2 derives queued/active/expired notification text from the existing record.
- G1 omits sleeping status, ancestry, recent memories, food stock and death totals.
  G2 displays existing fields without adding persistent data.
- During the first G2 capture, the inherited G1 overlay compositing drew every
  Rain tint, including wholly overridden duplicate Rain. That can make repeated
  nonstacking Rain look visually stronger and obscure Drought's winning tint.
  G2 will render each active area cell once using the existing Drought/earliest-ID
  precedence. This is a visual correction; resource semantics and accounting are
  not changed. The corresponding dominance is covered by a presentation test.

No verified simulation, biology, scheduler or save-format defect has been found.
The initial legacy-writer verification harness needed a `__file__` binding to run
an old module that derives its research path from that value; it failed before
writing evidence, was corrected, and is not a G1 defect.
