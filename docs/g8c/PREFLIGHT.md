# G8C preflight

Starting main/HEAD: c88b2174de365d5920ef2c05bfd5fbcb23d97c05, clean working tree.
No changes since the accepted reference. Branch: feature/g8c-time-flows.
Remote: git@github.com:lokrez/gnome-fortress.git. No running/suspended/orphaned game
or checkpoint worker found. 62 GiB RAM, about 50 GiB available; 8 GiB swap unused;
49 GiB disk free; /tmp has about 30 GiB free (tmpfs).

Protected world: run-results/god-terrain/world.g5.sqlite. Read-only inspection uses
shared nonblocking existing session and writer lock gates. No lock or journal is
deleted. Current hash and size/mtime are in evidence/preservation-start.json.

Reuse the prior independent /tmp/gnome-deep-time/player-copy.g5.sqlite only after
verifying its actual payload hash and inode independence. No new giant copy is
needed. Original is never loaded into a World or advanced. Generated seed-1 26k
fixture remains available under /tmp/gnome-g8a2-generated-fixtures.

Read the G8A2 architecture and Deep Time results; audit existing Chronicle,
worker, owner loop, serializer, storage, terrain model and file ownership. First
instrument actual bind/block/encode/prepare/detach, cold and warm boundaries, GC
callbacks and call profiles. Preserve source baseline for matched reference runs.
Scope is disposable snapshot preparation/IPC, not biology, gameplay or storage.
