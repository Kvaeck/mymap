# Model design (mymap.model)

This document describes the pure-Python domain model for MyMap. The goal is to keep business logic
(testable, deterministic) separate from Qt-based view code.

## Concepts

### Node
- `id: str` (UUID or stable string)
- `text: str`
- `x: float`
- `y: float`
- `meta: dict` (optional arbitrary metadata, e.g., color, style, collapsed)

### Edge
- `id: str` (optional)
- `src: str` (source node id)
- `dst: str` (destination node id)
- `meta: dict` (optional)

### Graph
Primary container:
- `nodes: Dict[str, Node]`
- `edges: List[Edge]`

Graph responsibilities:
- Add/remove nodes and edges.
- Validate that edges reference existing nodes.
- Provide serialization-friendly representation (dict).
- Simple helpers: find_node_by_text, neighbors(node_id), degree(node_id).

## JSON schema (high level)
```json
{
  "version": 1,
  "nodes": [
    {"id": "n1", "x": 10.0, "y": 20.0, "text": "Root", "meta": {}}
  ],
  "edges": [
    {"src": "n1", "dst": "n2", "meta": {}}
  ]
}
version should be incremented when schema changes. Implement migration strategies in io/persistence.

Implementation notes (non-prescriptive)
Keep the model fully independent of PySide/PyQt.

Commands should operate on the model; the scene should react to model changes and update gfx items.

Provide to_dict() / from_dict() methods on model classes for easy persistence and testing.
