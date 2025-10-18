# MyMap

MyMap is a mind-mapping desktop application prototype built with Python + PySide6.
This repository is organized with a modern `src/` layout for easy packaging and development.

## Quickstart (developer)

Requirements:
- Python 3.9+ (pyproject requires >=3.9)
- pip, virtualenv (recommended)
- On macOS: Xcode Command Line Tools (`xcode-select --install`) may be required.

1. Create and activate a virtual environment (recommended)
```bash
python -m venv .venv
source .venv/bin/activate
Install the project in editable mode

python -m pip install --upgrade pip setuptools wheel
pip install -e .
Install dev dependencies

python -m pip install -r requirements.txt
Run the app


# runs the installed console entrypoint (editable mode)
mymap

# or run as a module (bypasses installed scripts)
python -m mymap
Project layout (high-level)
bash
Copy code
src/mymap/             # main package
  ├── app.py           # app entrypoint (run)
  ├── __main__.py
  ├── ui/              # main_window & UI widgets
  ├── gfx/             # QGraphics items (Node/Edge/Canvas)
  ├── scene/           # scene glue (MindScene)
  ├── commands/        # undo/redo command implementations
  ├── model/           # pure-Python data model (Graph/Node/Edge)
  ├── io/              # persistence / import-export
  └── services/        # autosave & background tasks
tests/                  # unit & integration tests
docs/                   # design docs & onboarding
Development workflow
Use feature branches named like feature/xyz or chore/xyz.

Run tests with pytest.

Use pre-commit hooks (if configured) before pushing.

Contributing
See docs/onboarding.md for a short dev onboarding guide and docs/architecture.md for overall design.

