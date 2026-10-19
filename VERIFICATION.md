# Verification record

Host: Ubuntu 26.04.1 LTS, Linux x86_64. Python 3.14.4, SQLite 3.46.1,
pygame-ce 2.5.8 / SDL 2.32.10, pytest 9.1.1. Exact installed Python packages are
listed in `requirements-tested.txt`.

## Automated checks

Final command, run on 2026-10-19:

```bash
.venv/bin/python -m pytest -q -s
```

**27 passed in 164.92 seconds**, with no failures or skips. The endurance test took
132.608 seconds. Its final digest and all event/population counts matched an earlier
independent run of the same final engine rules.

The tests cover:

- Independent deterministic replay for three seeds; chunked versus single-tick
  execution; independence from global RNG and process hash seed.
- SQLite checkpoint equality at ticks 0, 91 and 500, followed by matching
  continuation and repeated snapshot replacement.
- Permanent death, old age, need-related mortality, founder count, unique identities,
  valid ancestry, inherited variation, and complete birth/death population accounting.
- Sleeping, early need-driven waking, retained memory, 60-slot fairness under
  oversubscription, unique assignments and newborn eligibility.
- A paired memory intervention and a separate inherited-curiosity intervention.
- Directional relationships and naturally occurring reproduction, social encounters,
  hazards and deaths.
- SQLite integrity, foreign keys, queryable records, rollback after an injected
  write failure, read-only missing-file handling and explicit connection closure.
- Command-line resumption and SIGINT shutdown at completed tick boundaries.
- Automated offscreen Pygame rendering, inspection, pause, single step, speed,
  save request, shutdown and equality with an unobserved simulation.
- Twenty thousand accelerated ticks with invariants checked every 500 ticks,
  followed by SQLite save/load, another 100 ticks and exact continuation equality.

## Measured memory effect

100 paired trials isolate one agent after a real hazard encounter. Both copies
have identical traits, needs, visits, peers, world and RNG. One copy retains its
learned movement association; the other has only associations erased.

| Condition | Subsequent hazard choices |
|---|---:|
| Experienced association retained | 0 / 100 |
| Association erased | 54 / 100 |

Inherited caution is fixed at zero and competing resource/social incentives are
removed in this test. This validates that the implemented consequence association
changes a controlled choice. It does not establish general intelligence, adaptive
culture or improved lifetime survival.

## Endurance result

Seed **2026**, final tick **20,100**, final world digest:

```
18abcc54608881c6892e1b913cd2b56d6288068afb4515f3467e94cab3c9696e
```

| Quantity | Measured count |
|---|---:|
| Living identities | 359 |
| Total births (including 60 founders) | 4,069 |
| Permanent deaths | 3,710 |
| Reproduction events | 4,009 |
| Hazard encounters | 6,148 |
| Social interactions | 26,113 |
| Sleep events | 91,428 |
| Wake events | 91,057 |

Unmatched sleep/wake counts include ongoing sleep and deaths during sleep. These
are event counters, not claims of emergent social structure. The run spans multiple
maximum lifespans and thousands of births; it is not a proof of indefinite
resource-bounded operation. Full archives grow over time as documented in
`ARCHITECTURE.md`.

## Observer smoke check

The bounded viewer command completed, checkpointed and exited using SDL's dummy
video driver. A rendered frame at seed 1, tick 180 was also inspected for readability.
The live desktop window has not been manually exercised; controls and rendering
are validated by automated Pygame event tests. The viewer displays actual model
state and performs no independent simulation.
