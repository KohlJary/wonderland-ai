# python-cli — Click-based command-line app skeleton

Minimal `click` + `pytest` scaffold. The hello-world is a `greet`
command that prints to stdout. The team extends this with new
commands, subcommands, options, etc.

## What's here

- `src/cli.py` — entry point with one `greet --name <NAME>` command
- `src/__init__.py` — package marker
- `tests/test_cli.py` — verifies `greet` runs and produces expected output
- `tests/conftest.py` — pytest fixtures (Click's `CliRunner`)
- `pyproject.toml` — declares `click >=8`, `pytest >=8`
- `.gitignore` — Python build artifacts + venv

## What's intentionally left undone

- No subcommand groups (intentional — pick once you have ≥3 commands)
- No config file loading (intentional — pick `tomli` / `pydantic-settings` / etc. when needed)
- No logging setup (intentional — `print` works for v1; introduce
  `logging` when there's a destination beyond stderr)

## Running

```bash
pip install -e .
python -m src.cli greet --name World
pytest
```
