# Fullstack starter — FastAPI + SQLAlchemy + SQLite + React + Vite

A working hello-world fullstack application. The backend serves
`/health` and `/api/messages` (a placeholder echo endpoint); the
frontend renders a one-message UI that fetches from the backend.
The team's job is to build features on top of this — the stack,
project layout, build config, and test framework are decided.

## Layout

```
src/backend/
  __init__.py
  main.py             # FastAPI app + lifespan
  db.py               # SQLAlchemy engine + sessionmaker
  models.py           # Base + an example HelloMessage model
  api/
    __init__.py       # router aggregation
    health.py         # /health
    messages.py       # /api/messages — echo endpoint, replace
                      #                  with real feature work
frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.tsx          # React entrypoint
    App.tsx           # one-message UI demonstrating end-to-end fetch
    api.ts            # fetch wrapper for backend calls
tests/
  __init__.py
  test_health.py      # baseline test — /health responds
  test_messages.py    # baseline test — POST /api/messages echoes
pyproject.toml         # Python deps + pytest config
.gitignore             # node_modules, __pycache__, *.db, dist/
```

## What's intentionally NOT here

- Authentication / sessions. (If the project needs it, the team
  builds it on top — see `python-fastapi-sqlite` or roll your own
  against the existing `db.py`.)
- Real domain models. `HelloMessage` is a placeholder showing the
  SQLAlchemy + Pydantic + endpoint-handler pattern; the team
  replaces it with the actual feature models.
- Frontend routing, state management, styling. One component,
  one fetch, one render. Add `react-router`, `zustand`, `tailwind`,
  whatever — those are choices for the architecture phase.
- Migrations. SQLite + `Base.metadata.create_all()` on startup is
  fine for development; production deployment would add Alembic.
- CI configuration. The pyproject.toml + package.json are
  testable locally; CI is a separate concern.

## How the team should approach it

1. `read_file pyproject.toml` and `read_file package.json` to see
   what's already installed.
2. `read_file src/backend/api/messages.py` and
   `read_file frontend/src/App.tsx` to see the existing pattern.
3. Architectural decisions (Cat ADRs) should explain how the
   feature *extends* this stack, not why a different stack would
   be better.
4. Tweedles `write_file` new feature files alongside the existing
   ones (don't overwrite the placeholders unless they're literally
   in the way).
5. Caterpillar reviews `git_diff HEAD` — the diff is the team's
   work, the seed is the baseline.

## Running it (for human verification, NOT for the team)

```bash
# Backend
pip install -e .
uvicorn src.backend.main:app --reload
# → http://localhost:8000/health → {"status": "ok"}
# → http://localhost:8000/docs   → Swagger UI

# Frontend
cd frontend && npm install && npm run dev
# → http://localhost:5173 — fetches /api/messages and renders
```

The team doesn't run these — they just `read_file` and `write_file`.
The runtime check is for humans verifying the seed works.
