# G6 — The Hand That Heals

PASS. Added two opt-in terrain powers with unchanged biology and no RNG draws.

- **Rewild**: radius 2, hazard only → forest, food initially zero. Existing food
  pulses subsequently regenerate it, including existing Rain/Drought rules.
- **Wellspring**: radius 0, rock only → water. All other targets are accepted as
  explicit zero-change requests. Nonzero radii are rejected. No walkable ground
  becomes water, no retained identity moves or drowns. Adjacency and drinking
  use inherited engine code, not a synthetic drinking event.

Both run in accepted global ID order at the next complete-tick boundary. Rewild
can transform newly ruptured ground in that same ordered batch. Reverse order
can instead leave hazard. Every transition remains; no deaths, injuries, learned
associations or objective events are reversed. Historical restoration is a new
physical action, never rollback. No resurrection/healing or guaranteed benefit.

Executed evidence: [targeted tests](targeted-tests.txt) includes foundation,
Rupture and restoration checks. Controlled isolated tests cover zero direct
health/displacement/resurrection, both action orders, Rain/Rewild and
Drought/Rewild at regeneration boundaries, real inherited drinking, zero-change
and repeated springs, pending/completed save/reload and exact replay. Fixtures
that isolate biology/decisions are explicitly test fixtures, not emergent claims.

Runnable natural seeded demonstration:

```bash
.venv/bin/python -m research.g6_demo --output run-results/g6-demo
```

[Actual output](demo.json) includes each ordered transition, continuation digest
and earlier death records retained. Target spring is chosen before the run using
the first row-major rock adjacent to traversable terrain. No site is selected for
dramatic outcomes. The future G7 presentation gate exposes complete controls;
this commit adds no partial UI. Legacy and research source remain unchanged.
