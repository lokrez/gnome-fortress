# Decision audit (G8B)

Baseline: bf6e5568056e75f07cd7b9d468a592fc5e5abf6f, clean main.
Read-only process inspection found owner 402014 and writer 402234. Neither was opened, signalled or used for testing.

`engine.py:World.step` increments time and regenerates resources every tenth tick,
then applies biology to every living individual. Biology ages, changes needs,
reduces fatigue during sleep, heals under qualifying conditions, and can kill
before scheduling. Wake events are separate from decisions.

`schedule` sorts eligible awake identities, rotates after the identity cursor,
and assigns at most 60 slots. Births wait until the next tick. Sleep releases a
slot immediately. No slot means no decision; it does not mean waiting.

`decide` uses ordered rules: thirst >=30 with accessible water; hunger >=30 with
local food >=10; fatigue >=65 with hunger <80 and thirst <75; reproduction;
social interaction; movement fallback. Reproduction checks the actor and each
local awake partner, then draws once for each eligible partner until successful.
It also draws inherited variation for a successful birth. Social interaction
checks nearby peers and needs before its probability draw, then draws a partner.
These are not competing utility scores.

`move` evaluates passable N/E/S/W neighbors. Scores combine curiosity or repeat
visits, Manhattan direction toward locally observed food/water weighted by needs,
qualifying nearby peers weighted by sociability, inherited hazard caution, and
learned `move:<terrain>` values. Python integer floor division is authoritative.
`rng.choice` is called even for a unique best candidate. No candidates means an
actual scheduled wait. Entering hazard draws damage, records an episode and
objective event, and can kill immediately.

`remember` appends an episode, keeps 64, and updates the association with
`clamp((3*old+reward)//4,-100,100)`. Zero reward can still change an association.
Social and reproduction decisions can change another individual's needs,
relationships and family counters. Objective history is distinct from bounded
agent memory and from the proposed disposable player observation.

TerrainWorld applies queued interventions in ID order before World.step. Neither
observer nor UI is permitted to request extra actions while explaining them.
Chronicle owns disposable mutation tracking; snapshots flatten the authoritative
world graph. Observation must not be attached to that graph.
