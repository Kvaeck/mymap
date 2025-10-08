# IO / Persistence

This document describes save/load behavior and JSON schema stability guarantees.

## File format
- Files are JSON with top-level structure:
  - `version` (int): schema version
  - `nodes` (list)
  - `edges` (list)

Example:
```json
{
  "version": 1,
  "nodes": [{"id":"n1","x":10,"y":20,"text":"A","meta":{}}],
  "edges": [{"src":"n1","dst":"n2","meta":{}}]
}
Versioning / migrations
version must be present.

io module should implement migrate(data: dict) -> dict which upgrades older versions to the latest schema.

Keep small, well-documented migration steps (1→2, 2→3, ...).

Backups & safety
On save, write to a temporary file and rename atomically.

Keep a rotating backup history (e.g., map.mymap.bak, map.mymap.bak1).

Validate loaded JSON before applying to live model.

Export / import adapters
Implement adapters in io/ for:

JSON (native)

Freemind (import)

PDF/PNG export (use Qt render via QPrinter / QPixmap)

Tests and examples
Keep example files in examples/ for testing import/export.

Add unit tests that round-trip model -> json -> model and assert equality for deterministic fields.
