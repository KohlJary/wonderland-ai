# Personal Markdown Notebook — FastAPI + React + SQLite

A fullstack starter application for building a personal markdown notebook web app.

**Stack:**
- Backend: Python + FastAPI + SQLAlchemy + SQLite
- Frontend: React + Vite + TypeScript + react-markdown
- No authentication — single user, persistent local storage

**Features:**
- Create, edit, and delete markdown notes with tags
- List notes, sorted by most-recently-edited
- Filter notes by tag
- Search notes by title, body, or tags
- Preview markdown to HTML in real-time (code blocks, headers, lists, links, images, blockquotes)
- Persistent storage across server restarts

---

## Quick Start — 5-Minute Setup

### Prerequisites
- Python 3.11+
- Node 14+ (for frontend)
- `pip` and `npm`

### Step 1: Clone and Install

```bash
git clone <repository-url>
cd mvp-demo-redux

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Start the Backend

In one terminal, from the project root:

```bash
uvicorn src.backend.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 3: Verify the Backend (Optional)

In another terminal, test the health endpoint:

```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### Step 4: Start the Frontend

From the project root (or in a third terminal):

```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

### Step 5: Open the App

Navigate to **http://localhost:5173** in your browser.

You now have a working fullstack app. Create a note, add tags, save it, and refresh the page — your note will persist.

---

## Project Layout

```
src/backend/
  __init__.py
  main.py              # FastAPI app + lifespan
  db.py                # SQLAlchemy engine + sessionmaker
  models.py            # SQLAlchemy models (Note, etc.)
  api/
    __init__.py        # router aggregation
    health.py          # /health endpoint
    notes.py           # /api/notes CRUD endpoints

frontend/
  package.json
  vite.config.ts
  tsconfig.json
  index.html
  src/
    main.tsx           # React entrypoint
    App.tsx            # Root component
    api.ts             # Fetch wrapper for backend calls
    components/        # React components
    ...

tests/
  __init__.py
  test_health.py       # Backend health tests
  test_notes.py        # Backend CRUD tests

pyproject.toml         # Python project config + deps
requirements.txt       # Pinned Python dependencies
.gitignore            # node_modules, __pycache__, *.db, dist/
```

---

## What's Here (and What Isn't)

### Included
- FastAPI + SQLAlchemy + SQLite project structure
- Basic CORS configuration for Vite dev server (localhost:5173)
- Database auto-initialization on startup
- Health check endpoint for monitoring
- Pytest + httpx for testing

### Excluded (By Design)
- **Authentication / sessions** — Single-user app; the team adds auth if needed later.
- **Real-time collaboration** — Single device; you can add WebSockets later.
- **Database migrations** — SQLite + `Base.metadata.create_all()` is fine for v1. Alembic is a next step if needed.
- **Styling framework** — The frontend is unstyled; add Tailwind, styled-components, etc. as needed.
- **Frontend routing** — App uses a single-page view for now; add react-router if you build a more complex UI.

---

## How the Team Should Approach It

1. **Read the existing code** — `src/backend/main.py`, `src/backend/models.py`, `frontend/src/App.tsx` show the pattern.
2. **Add feature models** — Replace the placeholder `HelloMessage` with real models like `Note`, `Tag`, etc.
3. **Write CRUD endpoints** — Extend `src/backend/api/notes.py` with POST, GET, PUT, DELETE handlers.
4. **Build React components** — Add Note editor, tag filter, search input alongside the existing App.
5. **Add tests** — Write tests in `tests/test_notes.py` to verify endpoints work.

The seed is a working baseline; your job is to build features on top of it.

---

## Running the App

### Backend Only

```bash
pip install -r requirements.txt
uvicorn src.backend.main:app --reload
# → http://localhost:8000/health
# → http://localhost:8000/docs (Swagger UI)
```

### Full Stack (Recommended)

1. Start backend: `uvicorn src.backend.main:app --reload`
2. In another terminal, start frontend: `cd frontend && npm run dev`
3. Open http://localhost:5173

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

---

## Database

The app uses SQLite, stored locally in `app.db` at the project root.

- The schema is created automatically on first startup.
- The database persists across server restarts.
- To reset data, delete `app.db` and restart the backend.

---

## Next Steps (For the Team)

1. **Schema** — Design the `notes` table with columns: `id`, `title`, `body`, `tags`, `created_at`, `updated_at`.
2. **CRUD Endpoints** — Implement POST `/api/notes`, GET `/api/notes`, GET `/api/notes/{id}`, PUT `/api/notes/{id}`, DELETE `/api/notes/{id}`.
3. **Frontend Components** — Build NoteEditor, NoteList, TagFilter, SearchBar.
4. **Search & Filter** — Implement tag filtering and full-text search on the backend.
5. **Markdown Preview** — Render markdown to HTML in the frontend.
6. **Polish** — Add styling, error handling, loading states.

---

## Notes for Reviewers

The seed provides a working fullstack baseline: project structure, CORS, database setup, and health check. The Tweedles' job is to replace the placeholder `HelloMessage` with real domain models and build feature endpoints on top.

When reviewing:
- `git diff HEAD` shows the team's work relative to this seed.
- The README above documents how to run the app — devs should follow these exact steps.
- The scaffold is intentionally minimal (no auth, no migrations, no styling); features are built incrementally.
