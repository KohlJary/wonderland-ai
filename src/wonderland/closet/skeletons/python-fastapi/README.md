# python-fastapi — FastAPI backend-only skeleton

Backend-only Python skeleton. The hello-world is a `/health`
endpoint that returns 200; tests use FastAPI's `TestClient` to
exercise the route. Pair with `react-vite` (frontend-only) for a
fullstack app, or extend solo for an API-only service.

## What's here

- `src/api.py` — FastAPI app with one `/health` endpoint
- `src/__init__.py` — package marker
- `tests/test_api.py` — TestClient-driven smoke test
- `tests/conftest.py` — fixtures (`client` = TestClient)
- `pyproject.toml` — declares `fastapi`, `httpx` (test client),
  `pytest`
- `.gitignore` — Python build artifacts + venv

## What's intentionally left undone

- No database (intentional — pick `sqlmodel` / `tortoise` /
  `sqlalchemy` when there's data worth persisting; `httpx` for
  external API calls)
- No auth (intentional — pick session-based or JWT when there's
  a user model; FastAPI's `Depends` makes the choice late)
- No CORS configuration (intentional — add `CORSMiddleware`
  with explicit origins when the frontend lands)
- No request logging beyond uvicorn's defaults (intentional —
  add `logging` config when there's a destination)

## Running

```bash
pip install -e .[dev]
uvicorn src.api:app --reload   # http://127.0.0.1:8000
pytest                         # run the test suite
```
