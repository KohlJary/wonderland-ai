# python-tui — Textual-based terminal UI app skeleton

Minimal `textual` + `pytest` scaffold. The hello-world is a single
screen with a counter + button; the team extends with new screens,
widgets, key bindings, etc.

## What's here

- `src/app.py` — `Textual` `App` subclass with a counter widget
- `src/__init__.py` — package marker
- `tests/test_app.py` — verifies the app mounts + counter increments
  via `app.run_test()` (Textual's pilot harness)
- `tests/conftest.py` — minimal pytest plumbing
- `pyproject.toml` — declares `textual>=8`, `pytest>=8`,
  `pytest-asyncio>=0.24` (Textual tests are async)
- `.gitignore` — Python build artifacts + venv

## What's intentionally left undone

- No CSS file (intentional — pick once you have ≥2 screens that
  share styling); inline `DEFAULT_CSS` works for v1
- No persistent state (intentional — start ephemeral, add a
  storage layer when there's data worth persisting)
- No keyboard-shortcut help screen (intentional — `Footer` already
  shows visible bindings; build a help screen when you have
  hidden ones)

## Running

```bash
pip install -e .[dev]
python -m src.app          # launch the TUI
pytest                     # run tests
```
