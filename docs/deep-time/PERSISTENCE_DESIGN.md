# Measured persistence changes

The accepted overwrite reconstructs the previous complete world twice. Retain
one full checksum/semantic validation **inside BEGIN IMMEDIATE**, eliminating
only the redundant outside reconstruction. Before opening for write, inspect
format/schema/one-row metadata using a read-only connection. Capture the file's
device/inode and metadata. Recheck both in the transaction; fail on replacement
or changed metadata. Open existing files with `mode=rw`, never implicit creation.
Check identity again before writing and after commit. The lifetime Saveguard
owner/writer locks remain mandatory at their existing call sites.

Do not cache validation receipts: a cold save still rehydrates the previous world
once. This deliberately avoids a second integrity-cache protocol. Release that
previous world before writing rather than retaining it through commit.

Serialize the current validated world using a shallow canonical projection and
JSON's dataclass default handler. Visit each actual field once; do not first
recursively deepcopy every episode, event and agent. Lists of record references
are temporary and read only during serialization. The worker receives an already
detached world; the final owner save happens after stepping stops. No background
reader receives mutable live objects.

Require exact bytes versus the established `json.dumps(world.state(),
sort_keys=True,separators=(',',':'))`, including Chronicle subclasses and integer
relationship keys. Preserve unknown TerrainWorld subclass state overrides through
the existing path. No schema, logical fields, hashing, FULL sync, publication,
checkpoint recovery or simulation changes. No history removal. These changes
reduce verified worker/finalization costs; they do not by themselves prove a
smaller main-thread snapshot pause.

The committed save result now returns its already computed canonical SHA-256.
`god_world` uses that exact committed digest in its final summary, avoiding a
second full canonical-state deepcopy/encoding solely to print the same checksum.
The scalar is returned only after commit/publication succeeds; it is not a new
checkpoint field. A targeted launcher test forbids a second `World.digest()` call.
