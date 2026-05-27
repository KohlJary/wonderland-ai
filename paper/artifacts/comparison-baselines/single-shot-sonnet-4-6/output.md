I'll build a complete personal markdown notebook web app. Let me create all the files needed.

```
markdown-notebook/
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   └── tests/
│       ├── __init__.py
│       └── test_api.py
└── frontend/
    ├── package.json
    ├── tsconfig.json
    ├── tsconfig.node.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        ├── api.ts
        ├── types.ts
        └── components/
            ├── NoteList.tsx
            ├── NoteEditor.tsx
            ├── NoteViewer.tsx
            ├── SearchBar.tsx
            └── TagFilter.tsx
```

---

```markdown
# Markdown Notebook

A personal markdown notebook — create, tag, search, and browse notes that persist across sessions.

## Prerequisites

- Python 3.11+
- Node.js 18+

## Run the Demo (< 5 minutes)

### 1. Clone & enter the repo

```bash
git clone <repo-url> markdown-notebook
cd markdown-notebook
```

### 2. Start the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn main:app --reload --port 8000
```

The API is now running at http://localhost:8000.  
Interactive docs: http://localhost:8000/docs

### 3. Start the frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser — the notebook is ready.

### 4. Run backend tests

```bash
cd backend
pytest -v
```

## Features

- **Create / Edit / Delete** notes with a title, markdown body, and optional tags
- **Live preview** — rendered markdown beside the editor (code, headers, lists, links, images, blockquotes)
- **Search** — substring search across title, body, and tags
- **Tag filter** — click any tag to filter the note list
- **Persistent** — SQLite file (`notebook.db`) survives server restarts

## Project Structure

```
backend/   FastAPI + SQLite (uvicorn)
frontend/  React + Vite + TypeScript (npm run dev)
```

Vite proxies `/api/*` → `http://localhost:8000` so there are no CORS issues in development.
```

---

```toml
# backend/pyproject.toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "markdown-notebook-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.29.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "pytest-asyncio>=0.23.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///./notebook.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

```python
# backend/models.py
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Table, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base

# Association table for the many-to-many between notes and tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, nullable=False, index=True)

    notes = relationship("Note", secondary=note_tags, back_populates="tags")


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(256), nullable=False)
    body = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    tags = relationship("Tag", secondary=note_tags, back_populates="notes", lazy="joined")
```

---

```python
# backend/schemas.py
from datetime import datetime
from pydantic import BaseModel, Field


class TagOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(default="")
    tags: list[str] = Field(default_factory=list)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(NoteBase):
    pass


class NoteOut(BaseModel):
    id: int
    title: str
    body: str
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

---

```python
# backend/crud.py
from datetime import datetime, timezone

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from models import Note, Tag
from schemas import NoteCreate, NoteUpdate


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _get_or_create_tags(db: Session, tag_names: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags


# ---------------------------------------------------------------------------
# notes
# ---------------------------------------------------------------------------

def get_note(db: Session, note_id: int) -> Note | None:
    return db.query(Note).filter(Note.id == note_id).first()


def list_notes(
    db: Session,
    search: str | None = None,
    tag: str | None = None,
) -> list[Note]:
    q = db.query(Note)

    if tag:
        tag = tag.strip().lower()
        q = q.join(Note.tags).filter(Tag.name == tag)

    if search:
        pattern = f"%{search}%"
        # Search in title, body, and tag names
        q = (
            q.outerjoin(Note.tags)
            .filter(
                or_(
                    Note.title.ilike(pattern),
                    Note.body.ilike(pattern),
                    Tag.name.ilike(pattern),
                )
            )
            .distinct()
        )

    return q.order_by(Note.updated_at.desc()).all()


def create_note(db: Session, payload: NoteCreate) -> Note:
    tags = _get_or_create_tags(db, payload.tags)
    note = Note(title=payload.title, body=payload.body, tags=tags)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def update_note(db: Session, note: Note, payload: NoteUpdate) -> Note:
    note.title = payload.title
    note.body = payload.body
    note.tags = _get_or_create_tags(db, payload.tags)
    note.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: Note) -> None:
    db.delete(note)
    db.commit()


def list_all_tags(db: Session) -> list[Tag]:
    return db.query(Tag).order_by(Tag.name).all()
```

---

```python
# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import engine, get_db

# Create tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Markdown Notebook API", version="0.1.0")

# CORS — only needed when frontend dev server is on a different port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

@app.get("/api/notes", response_model=list[schemas.NoteOut])
def list_notes(
    search: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return crud.list_notes(db, search=search, tag=tag)


@app.post("/api/notes", response_model=schemas.NoteOut, status_code=201)
def create_note(payload: schemas.NoteCreate, db: Session = Depends(get_db)):
    return crud.create_note(db, payload)


@app.get("/api/notes/{note_id}", response_model=schemas.NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/api/notes/{note_id}", response_model=schemas.NoteOut)
def update_note(note_id: int, payload: schemas.NoteUpdate, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return crud.update_note(db, note, payload)


@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = crud.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    crud.delete_note(db, note)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@app.get("/api/tags", response_model=list[schemas.TagOut])
def list_tags(db: Session = Depends(get_db)):
    return crud.list_all_tags(db)
```

---

```python
# backend/tests/__init__.py
```

---

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def make_note(title="Test Note", body="Hello **world**", tags=None):
    payload = {"title": title, "body": body, "tags": tags or []}
    resp = client.post("/api/notes", json=payload)
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------

class TestCreateNote:
    def test_creates_note_with_tags(self):
        data = make_note(title="My Note", body="# Heading", tags=["python", "dev"])
        assert data["title"] == "My Note"
        assert data["body"] == "# Heading"
        assert {t["name"] for t in data["tags"]} == {"python", "dev"}
        assert data["id"] > 0

    def test_creates_note_without_tags(self):
        data = make_note(title="No Tags", tags=[])
        assert data["tags"] == []

    def test_title_required(self):
        resp = client.post("/api/notes", json={"body": "body only"})
        assert resp.status_code == 422

    def test_empty_title_rejected(self):
        resp = client.post("/api/notes", json={"title": "", "body": "x"})
        assert resp.status_code == 422


class TestGetNote:
    def test_get_existing(self):
        created = make_note(title="Fetch Me")
        resp = client.get(f"/api/notes/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Fetch Me"

    def test_get_missing(self):
        resp = client.get("/api/notes/999999")
        assert resp.status_code == 404


class TestUpdateNote:
    def test_update_title_and_body(self):
        note = make_note(title="Old Title")
        resp = client.put(
            f"/api/notes/{note['id']}",
            json={"title": "New Title", "body": "new body", "tags": []},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    def test_update_replaces_tags(self):
        note = make_note(tags=["a", "b"])
        resp = client.put(
            f"/api/notes/{note['id']}",
            json={"title": note["title"], "body": note["body"], "tags": ["c"]},
        )
        names = {t["name"] for t in resp.json()["tags"]}
        assert names == {"c"}

    def test_update_missing_note(self):
        resp = client.put(
            "/api/notes/999999",
            json={"title": "x", "body": "", "tags": []},
        )
        assert resp.status_code == 404


class TestDeleteNote:
    def test_delete_existing(self):
        note = make_note()
        resp = client.delete(f"/api/notes/{note['id']}")
        assert resp.status_code == 204
        assert client.get(f"/api/notes/{note['id']}").status_code == 404

    def test_delete_missing(self):
        resp = client.delete("/api/notes/999999")
        assert resp.status_code == 404


class TestListNotes:
    def test_returns_most_recently_edited_first(self):
        n1 = make_note(title="First")
        n2 = make_note(title="Second")
        # Update n1 so it is now the most recent
        client.put(
            f"/api/notes/{n1['id']}",
            json={"title": "First Updated", "body": "", "tags": []},
        )
        resp = client.get("/api/notes")
        assert resp.status_code == 200
        titles = [n["title"] for n in resp.json()]
        assert titles[0] == "First Updated"

    def test_empty_list(self):
        resp = client.get("/api/notes")
        assert resp.json() == []


class TestSearch:
    def test_search_by_title(self):
        make_note(title="FastAPI guide", body="something else")
        make_note(title="React tutorial")
        resp = client.get("/api/notes?search=fastapi")
        results = resp.json()
        assert len(results) == 1
        assert results[0]["title"] == "FastAPI guide"

    def test_search_by_body(self):
        make_note(title="Note A", body="sqlalchemy is great")
        make_note(title="Note B", body="nothing special")
        resp = client.get("/api/notes?search=sqlalchemy")
        assert len(resp.json()) == 1

    def test_search_by_tag(self):
        make_note(title="Tagged", tags=["rust"])
        make_note(title="Untagged")
        resp = client.get("/api/notes?search=rust")
        assert len(resp.json()) == 1

    def test_search_no_results(self):
        make_note(title="something")
        resp = client.get("/api/notes?search=zzznomatch")
        assert resp.json() == []


class TestTagFilter:
    def test_filter_by_tag(self):
        make_note(title="Python note", tags=["python"])
        make_note(title="JS note", tags=["javascript"])
        resp = client.get("/api/notes?tag=python")
        results = resp.json()
        assert len(results) == 1
        assert results[0]["title"] == "Python note"

    def test_filter_no_match(self):
        make_note(title="A note", tags=["go"])
        resp = client.get("/api/notes?tag=haskell")
        assert resp.json() == []


class TestTagsEndpoint:
    def test_lists_all_tags(self):
        make_note(tags=["alpha", "beta"])
        make_note(tags=["gamma"])
        resp = client.get("/api/tags")
        assert resp.status_code == 200
        names = {t["name"] for t in resp.json()}
        assert {"alpha", "beta", "gamma"} <= names

    def test_tags_deduplicated(self):
        make_note(tags=["shared"])
        make_note(tags=["shared"])
        resp = client.get("/api/tags")
        tag_names = [t["name"] for t in resp.json()]
        assert tag_names.count("shared") == 1
```

---

```json
// frontend/package.json
{
  "name": "markdown-notebook-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "rehype-highlight": "^7.0.0",
    "highlight.js": "^11.9.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "typescript": "^5.4.5",
    "vite": "^5.3.1"
  }
}
```

---

```json
// frontend/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

```json
// frontend/tsconfig.node.json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

---

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

---

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Markdown Notebook</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>📓</text></svg>" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

---

```typescript
// frontend/src/types.ts
export interface Tag {
  id: number;
  name: string;
}

export interface Note {
  id: number;
  title: string;
  body: string;
  tags: Tag[];
  created_at: string;
  updated_at: string;
}

export interface NotePayload {
  title: string;
  body: string;
  tags: string[];
}
```

---

```typescript
// frontend/src/api.ts
import type { Note, NotePayload, Tag } from "./types";

const BASE = "/api";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listNotes(params?: { search?: string; tag?: string }): Promise<Note[]> {
    const qs = new URLSearchParams();
    if (params?.search) qs.set("search", params.search);
    if (params?.tag) qs.set("tag", params.tag);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return request<Note[]>(`/notes${query}`);
  },

  getNote(id: number): Promise<Note> {
    return request<Note>(`/notes/${id}`);
  },

  createNote(payload: NotePayload): Promise<Note> {
    return request<Note>("/notes", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateNote(id: number, payload: NotePayload): Promise<Note> {
    return request<Note>(`/notes/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteNote(id: number): Promise<void> {
    return request<void>(`/notes/${id}`, { method: "DELETE" });
  },

  listTags(): Promise<Tag[]> {
    return request<Tag[]>("/tags");
  },
};
```

---

```css
/* frontend/src/index.css */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

:root {
  --bg: #0f1117;
  --surface: #1a1d27;
  --surface2: #22263a;
  --border: #2e3347;
  --primary: #7c6af7;
  --primary-dim: #5a4fcf;
  --danger: #e05c6a;
  --text: #e4e6f0;
  --text-dim: #8b90a8;
  --tag-bg: #252a40;
  --tag-text: #a8b0d8;
  --code-bg: #12141e;
  --radius: 8px;
  --sidebar-w: 300px;
  --font-mono: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
}

html, body, #root {
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--bg);
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
}

/* ── Layout ─────────────────────────────────────────── */
.app {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: var(--sidebar-w);
  min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-pane {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

/* ── Sidebar header ──────────────────────────────────── */
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar-title {
  font-size: 17px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.3px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.new-note-btn {
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  transition: background 0.15s;
}

.new-note-btn:hover {
  background: var(--primary-dim);
}

/* ── Search ──────────────────────────────────────────── */
.search-bar {
  padding: 10px 16px;
  border-bottom: 1px solid var(--border);
}

.search-input {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 7px 10px;
  color: var(--text);
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}

.search-input:focus {
  border-color: var(--primary);
}

.search-input::placeholder {
  color: var(--text-dim);
}

/* ── Tag filter ──────────────────────────────────────── */
.tag-filter {
  padding: 8px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-chip {
  background: var(--tag-bg);
  color: var(--tag-text);
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.1s;
  font-weight: 500;
  letter-spacing: 0.2px;
}

.tag-chip:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.tag-chip.active {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.tag-filter-label {
  font-size: 11px;
  color: var(--text-dim);
  margin-bottom: 4px;
  width: 100%;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ── Note list ───────────────────────────────────────── */
.note-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.note-list::-webkit-scrollbar { width: 4px; }
.note-list::-webkit-scrollbar-track { background: transparent; }
.note-list::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

.note-item {
  padding: 10px 16px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.1s, border-color 0.1s;
}

.note-item:hover {
  background: var(--surface2);
}

.note-item.selected {
  background: var(--surface2);
  border-left-color: var(--primary);
}

.note-item-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.note-item-preview {
  font-size: 11px;
  color: var(--text-dim