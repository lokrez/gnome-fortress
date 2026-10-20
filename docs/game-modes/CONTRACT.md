# Game Mode Design Contract

Status: intended release architecture; **design only**, G2. There are exactly three
intended release modes. None is implemented or selectable by this contract.
Current G1/G2 remains an explicitly unrestricted prototype with manual saving;
it is not a release-mode implementation.

## Ironman — Definitive Mode

Intended default for the finished game. One persistent, irreversible run timeline.
Player-facing manual rollback, earlier-save selection, intervention undo, timeline
branching and reseeding that run are disallowed. Powers become available through
versioned, explicit progression criteria satisfied by actual recorded world events.
Criteria are not designed in G2. Benevolent, tyrannical, indifferent and inconsistent
playstyles remain possible; no mandatory morality path or guaranteed civilization.

Global extinction permanently closes the run to simulation and intervention input.
A final chronicle retains identities, histories, interventions, provenance and the
final state for read-only inspection. Starting anew creates a different run, never
repopulates this one. Inspection must not change its canonical files or consume RNG.

**Technical failure recovery is allowed; reversing gameplay consequences is not.**
A crash, incomplete transaction or independently verified corruption may justify
controlled restoration from the newest verified compatible checkpoint followed by
validated journal replay. Drought, deaths, an earthquake in a future implementation,
or regret about a player decision are not technical failures. Extinction is not a
recovery trigger. Recovery cannot choose a preferred earlier outcome or delete an
accepted divine request merely because the consequence was harmful.

Use reasonable game enforcement: one canonical run, no in-game earlier-save menu,
validated checkpoint/journal chains, explicit recovery records and unambiguous
terminal status. A purely offline game **cannot make rollback cryptographically
impossible** for an owner who copies/modifies files, patches code or controls the
machine. Hashes detect accidental damage and help verify consistency; they are not
proof against the owner forging a history. Do not claim absolute tamper resistance.

## Standard — Flexible Mode

Same simulation, world-event progression and unlock criteria as Ironman. Manual
saves/reloads and revisiting earlier decisions are allowed. A reload restores the
entire corresponding logical state, including RNG, progression and intervention
history; it cannot combine an earlier world with later unlocks accidentally.
The UI must identify the loaded timeline position. This is suitable for ordinary
play and experimentation with consequences. Intelligence, learning weights,
biological difficulty and scheduler fairness are not weakened or strengthened by
the mode label. Optional future difficulty/world settings must be explicit inputs,
not hidden differences attributed to a mode.

Extinction ends the current simulated timeline and makes that terminal state
inspectable. Standard may explicitly load a pre-extinction manual save, which
revisits a decision history; stepping or casting in the terminal state itself
cannot resurrect it. Distinguish this permitted reload from continuing an extinct
world. Technical recovery still uses verified data rather than silent reseeding.

## Sandbox — Experimental Mode

Immediate access to every implemented divine power, without progression locks.
Allow supported world configurations and explicitly identified experimental
controls. Unsupported experiments are not silently simulated. Record consequential
settings and inputs so replay knows what changed. Sandbox may support manual saves,
reloads and explicit separate experimental branches; a branch/new world must be
identified rather than rewriting a claimed Ironman run.

The underlying simulation remains honest: no manufactured societies, belief,
intelligence or language, no hidden outcome scripts, no forced success. Baseline
rules remain common unless an explicitly supported experimental setting changes
a rule and records that setting/version. Experimental communication remains opt-in
and separate from production GameWorld. A mode name is not permission to merge
unverified research. Extinct states stay terminal; restart or loading a prior
state is explicit and never automatic founder respawning.

## Shared architecture requirements

### Identity, policy and presentation

A future versioned envelope must carry stable run identity, immutable release-mode
identity, simulation/rules version, settings/seed, save-format version and policy/
progression version. Mode is selected only when creating a new release-mode run;
there is no in-place conversion of an existing run. Sandbox/Standard copies must
never be relabeled Ironman or inherit its provenance claim. How to offer explicit
new-run imports remains future design, not an implicit migration operation.

Separate a small per-mode permission/progression policy from simulation rules.
The policy decides which player commands are permitted and which genuinely
recorded criteria unlock powers. The engine remains authoritative for biological
and environmental consequences. Presentation consumes these permissions and real
state; hiding a button cannot be the sole enforcement of a permission. Journal
accepted consequential commands with deterministic tick boundaries. For identical
initial state and accepted input sequence, mode presentation must not change the
simulation outcome. Nonconsequential inspection, scroll position and animation
need not enter canonical world state.

### Versioning and G1 legacy saves

Existing `.g1.sqlite` schema 1 / format `gnome-fortress-game-g1-v1` remains valid.
G2 changes no format or database bytes merely to attach UI telemetry. G1 has no
release-mode field and **must never silently become Ironman**. Identify it as a
legacy prototype, not a fourth intended release mode. Continue it through the
compatible prototype loader. If future release software offers import, require an
explicit new compatible Standard/Sandbox run identity with legacy provenance;
never overwrite the original or grant an Ironman history retroactively.

Future schema migration must be explicit, versioned, backed up, atomic and tested
for preservation of state/RNG/history/progression and unknown/unsupported versions.
Do not apply an engine behavior change while calling it a storage-only migration.
If behavior cannot be preserved, reject continuation or require an explicit new
run under new rules; retain the old reader for inspection/replay where feasible.
Checksums, identities and mode-policy versions must be validated before mutation.

### Checkpoints, journals and recovery

Keep initial settings and ordered accepted inputs sufficient for deterministic
replay, with implementation versions. Distinguish command acceptance, durable
journal acknowledgement and complete-tick checkpoint commitment. Before claiming
irreversible consequences, specify the crash-durability contract for acknowledged
commands. Checkpoints need verified logical state, RNG, tick, input sequence/
journal position, lineage and integrity digests. Journal records need unambiguous
IDs/order, intended tick boundaries and enough parameters to replay an accepted
command exactly once. Do not consume simulation RNG to assign UI/recovery identity.

On load: validate compatible format/rules, complete records, checksums and timeline
relationships. Fail closed on unsupported, incomplete or corrupt data; preserve
suspect files and show a useful diagnostic. Never silently replace a failed run
with new founders. Recovery must validate the newest recoverable checkpoint and
journal tail, replay accepted inputs without duplication, verify resulting state
where evidence exists, and record what was recovered or provably lost. Missing or
ambiguous journal data requires explicit failure/diagnosis, not invented events.
Recovery notices must distinguish technical reconstruction from gameplay rollback.

A known extinct timeline cannot be reopened by choosing an older checkpoint in
Ironman. Standard/Sandbox may use explicitly permitted reload policy. All modes
need a read-only final chronicle and an unambiguous global-extinction definition
(zero living agents, not merely an empty settlement). Preserve terminal tick,
identities, births/deaths, intervention history and final state. Opening that
chronicle must not auto-checkpoint, step time or request powers.

### Scope and implementation gate

This contract specifies requirements, not a choice of extra database services,
cryptographic identity infrastructure or a multi-process event-sourcing framework.
Prefer the smallest tested checkpoint/journal design that meets the eventual
contract. Progression criteria, release migration UX, recovery acknowledgement
semantics and chronicle UI require separate approval/design before implementation.

G2 implements **none** of: mode selectors, release-mode metadata, progression,
unlocks, new save formats/migrations, Ironman enforcement or recovery journals.
The prototype's transactional saves are not certification of crash recovery.
G3 and Ironman implementation remain unauthorized.
