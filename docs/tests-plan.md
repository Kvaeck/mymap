# Tests plan (priority)

## High priority (smoke / quick)
1. Importability test (already present).
2. Model round-trip: Graph -> to_dict -> from_dict -> Graph equality.
3. Scene serialization: create scene with 2 nodes + 1 edge -> to_json -> from_json -> same counts.

## Medium priority
4. Commands: AddNodeCommand, MoveNodeCommand, AddEdgeCommand undo/redo semantics.
5. IO safety: saving produces valid JSON and loads without exceptions.

## Integration (requires pytest-qt)
6. GUI integration tests (pytest-qt):
   - Adding nodes via toolbar produces nodes in scene.
   - Undo/redo restores selection and positions.

## How to run
- `pytest -q` (prefers a virtualenv with requirements-dev installed)
- For GUI tests use `pytest-qt` and run in an environment where a display is available (CI can use xvfb on Linux).

## Files to add
- `tests/unit/test_model.py`
- `tests/unit/test_commands.py`
- `tests/integration/test_scene_serialization.py`
