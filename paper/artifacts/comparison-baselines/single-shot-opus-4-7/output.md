# Personal Markdown Notebook

I'll build a complete markdown notebook app with FastAPI + SQLite backend and React + Vite + TypeScript frontend.

## Project Structure

```
notebook/
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   └── schemas.py
│   └── tests/
│       ├── __init__.py
│       └── test_api.py
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── api.ts
│       ├── types.ts
│       ├── styles.css
│       └── components/
│           ├── NoteList.tsx
│           └── NoteEditor.tsx
├── .gitignore
└── README.md
```

---

### Backend

```toml
# backend/pyproject.toml
[project]
name = "notebook-backend"
version = "0.1.0"
description = "Personal markdown notebook backend"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]
```

```python
# backend/app/__init__.py
```

```python
# backend/app/db.py
"""SQLite connection helpers and schema initialization."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

# Default DB path; overridable for tests via NOTEBOOK_DB_PATH.
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "notebook.db"


def get_db_path() -> Path:
    return Path(os.environ.get("NOTEBOOK_DB_PATH", str(DEFAULT_DB_PATH)))


SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (note_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_notes_updated_at ON notes(updated_at DESC);
"""


def init_db() -> None:
    """Create tables if they don't exist."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a configured SQLite connection."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

```python
# backend/app/schemas.py
"""Pydantic models for API requests/responses."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = ""
    tags: List[str] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen = set()
        for t in v:
            t2 = t.strip().lower()
            if t2 and t2 not in seen:
                seen.add(t2)
                cleaned.append(t2)
        return cleaned


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        cleaned: List[str] = []
        seen = set()
        for t in v:
            t2 = t.strip().lower()
            if t2 and t2 not in seen:
                seen.add(t2)
                cleaned.append(t2)
        return cleaned


class Note(BaseModel):
    id: int
    title: str
    body: str
    tags: List[str]
    created_at: str
    updated_at: str
```

```python
# backend/app/models.py
"""Data-access functions over SQLite."""
from __future__ import annotations

import sqlite3
from typing import List, Optional

from .db import get_conn


def _row_to_note(row: sqlite3.Row, tags: List[str]) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "tags": tags,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _tags_for_note(conn: sqlite3.Connection, note_id: int) -> List[str]:
    rows = conn.execute(
        """
        SELECT t.name FROM tags t
        JOIN note_tags nt ON nt.tag_id = t.id
        WHERE nt.note_id = ?
        ORDER BY t.name
        """,
        (note_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def _ensure_tags(conn: sqlite3.Connection, tags: List[str]) -> List[int]:
    ids: List[int] = []
    for name in tags:
        conn.execute("INSERT OR IGNORE INTO tags(name) VALUES (?)", (name,))
        row = conn.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        ids.append(row["id"])
    return ids


def _set_note_tags(conn: sqlite3.Connection, note_id: int, tags: List[str]) -> None:
    conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
    tag_ids = _ensure_tags(conn, tags)
    for tid in tag_ids:
        conn.execute(
            "INSERT OR IGNORE INTO note_tags(note_id, tag_id) VALUES (?, ?)",
            (note_id, tid),
        )
    # Clean up orphan tags
    conn.execute(
        """
        DELETE FROM tags
        WHERE id NOT IN (SELECT DISTINCT tag_id FROM note_tags)
        """
    )


def create_note(title: str, body: str, tags: List[str]) -> dict:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO notes(title, body) VALUES (?, ?)",
            (title, body),
        )
        note_id = cur.lastrowid
        _set_note_tags(conn, note_id, tags)
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return _row_to_note(row, _tags_for_note(conn, note_id))


def get_note(note_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        if row is None:
            return None
        return _row_to_note(row, _tags_for_note(conn, note_id))


def update_note(
    note_id: int,
    title: Optional[str],
    body: Optional[str],
    tags: Optional[List[str]],
) -> Optional[dict]:
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        if existing is None:
            return None

        new_title = title if title is not None else existing["title"]
        new_body = body if body is not None else existing["body"]
        conn.execute(
            """
            UPDATE notes
            SET title = ?, body = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_title, new_body, note_id),
        )
        if tags is not None:
            _set_note_tags(conn, note_id, tags)

        row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return _row_to_note(row, _tags_for_note(conn, note_id))


def delete_note(note_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        # Tag cleanup
        conn.execute(
            """
            DELETE FROM tags
            WHERE id NOT IN (SELECT DISTINCT tag_id FROM note_tags)
            """
        )
        return cur.rowcount > 0


def list_notes(
    q: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[dict]:
    with get_conn() as conn:
        sql = "SELECT DISTINCT n.* FROM notes n"
        params: List = []
        wheres: List[str] = []

        if tag:
            sql += " JOIN note_tags nt ON nt.note_id = n.id JOIN tags t ON t.id = nt.tag_id"
            wheres.append("t.name = ?")
            params.append(tag.strip().lower())

        if q:
            like = f"%{q.lower()}%"
            wheres.append(
                """
                (
                    lower(n.title) LIKE ?
                    OR lower(n.body) LIKE ?
                    OR EXISTS (
                        SELECT 1 FROM note_tags nt2
                        JOIN tags t2 ON t2.id = nt2.tag_id
                        WHERE nt2.note_id = n.id AND lower(t2.name) LIKE ?
                    )
                )
                """
            )
            params.extend([like, like, like])

        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY n.updated_at DESC, n.id DESC"

        rows = conn.execute(sql, params).fetchall()
        result = []
        for row in rows:
            result.append(_row_to_note(row, _tags_for_note(conn, row["id"])))
        return result


def list_tags() -> List[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT name FROM tags ORDER BY name").fetchall()
        return [r["name"] for r in rows]
```

```python
# backend/app/main.py
"""FastAPI app exposing CRUD + search for notes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .db import init_db
from .schemas import Note, NoteCreate, NoteUpdate

app = FastAPI(title="Personal Markdown Notebook")

# Allow the Vite dev server to call us directly (in addition to the proxy).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/notes", response_model=List[Note])
def list_notes(
    q: Optional[str] = Query(None, description="Substring search"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
) -> List[Note]:
    return [Note(**n) for n in models.list_notes(q=q, tag=tag)]


@app.post("/api/notes", response_model=Note, status_code=201)
def create_note(payload: NoteCreate) -> Note:
    note = models.create_note(payload.title, payload.body, payload.tags)
    return Note(**note)


@app.get("/api/notes/{note_id}", response_model=Note)
def get_note(note_id: int) -> Note:
    note = models.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(**note)


@app.put("/api/notes/{note_id}", response_model=Note)
def update_note(note_id: int, payload: NoteUpdate) -> Note:
    note = models.update_note(
        note_id,
        title=payload.title,
        body=payload.body,
        tags=payload.tags,
    )
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return Note(**note)


@app.delete("/api/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> None:
    if not models.delete_note(note_id):
        raise HTTPException(status_code=404, detail="Note not found")


@app.get("/api/tags", response_model=List[str])
def list_tags() -> List[str]:
    return models.list_tags()
```

```python
# backend/tests/__init__.py
```

```python
# backend/tests/test_api.py
"""End-to-end API tests using a temporary SQLite database."""
from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client():
    # Use a fresh DB file per test.
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["NOTEBOOK_DB_PATH"] = path

    # Import after env var is set so init picks it up.
    from app.main import app
    from app.db import init_db

    init_db()
    with TestClient(app) as c:
        yield c

    os.remove(path)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_list_note(client):
    r = client.post(
        "/api/notes",
        json={"title": "Hello", "body": "# heading", "tags": ["work", "Ideas"]},
    )
    assert r.status_code == 201
    note = r.json()
    assert note["title"] == "Hello"
    assert note["body"] == "# heading"
    assert sorted(note["tags"]) == ["ideas", "work"]

    r = client.get("/api/notes")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_update_note(client):
    r = client.post("/api/notes", json={"title": "A", "body": "x", "tags": ["t1"]})
    note_id = r.json()["id"]

    r = client.put(
        f"/api/notes/{note_id}",
        json={"title": "B", "body": "y", "tags": ["t2"]},
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["title"] == "B"
    assert updated["body"] == "y"
    assert updated["tags"] == ["t2"]


def test_delete_note(client):
    r = client.post("/api/notes", json={"title": "A", "body": "", "tags": []})
    note_id = r.json()["id"]

    r = client.delete(f"/api/notes/{note_id}")
    assert r.status_code == 204

    r = client.get(f"/api/notes/{note_id}")
    assert r.status_code == 404


def test_search_filters_by_title_body_and_tags(client):
    client.post("/api/notes", json={"title": "Postgres tricks", "body": "vacuum", "tags": ["db"]})
    client.post("/api/notes", json={"title": "Recipe", "body": "boil water", "tags": ["cooking"]})
    client.post("/api/notes", json={"title": "Misc", "body": "Postgres is in the body", "tags": []})

    r = client.get("/api/notes", params={"q": "postgres"})
    assert r.status_code == 200
    titles = {n["title"] for n in r.json()}
    assert titles == {"Postgres tricks", "Misc"}

    r = client.get("/api/notes", params={"q": "cooking"})
    assert {n["title"] for n in r.json()} == {"Recipe"}


def test_filter_by_tag(client):
    client.post("/api/notes", json={"title": "A", "body": "", "tags": ["x"]})
    client.post("/api/notes", json={"title": "B", "body": "", "tags": ["y"]})

    r = client.get("/api/notes", params={"tag": "x"})
    assert [n["title"] for n in r.json()] == ["A"]


def test_list_order_is_most_recently_edited_first(client):
    r1 = client.post("/api/notes", json={"title": "first", "body": "", "tags": []})
    r2 = client.post("/api/notes", json={"title": "second", "body": "", "tags": []})

    # Touch the first note to make it newer
    client.put(f"/api/notes/{r1.json()['id']}", json={"body": "updated"})

    titles = [n["title"] for n in client.get("/api/notes").json()]
    assert titles[0] == "first"
    assert titles[1] == "second"


def test_blank_title_rejected(client):
    r = client.post("/api/notes", json={"title": "   ", "body": "", "tags": []})
    assert r.status_code == 422


def test_tags_endpoint(client):
    client.post("/api/notes", json={"title": "A", "body": "", "tags": ["alpha", "beta"]})
    client.post("/api/notes", json={"title": "B", "body": "", "tags": ["beta"]})
    r = client.get("/api/tags")
    assert r.status_code == 200
    assert r.json() == ["alpha", "beta"]
```

---

### Frontend

```json
// frontend/package.json
{
  "name": "notebook-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.2",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "jsdom": "^24.1.0",
    "typescript": "^5.4.5",
    "vite": "^5.3.1",
    "vitest": "^1.6.0"
  }
}
```

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
    "noFallthroughCasesInSwitch": true,
    "types": ["vitest/globals"]
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

```json
// frontend/tsconfig.node.json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true,
    "strict": true
  },
  "include": ["vite.config.ts"]
}
```

```typescript
// frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
});
```

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Notebook</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```typescript
// frontend/src/types.ts
export interface Note {
  id: number;
  title: string;
  body: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface NoteInput {
  title: string;
  body: string;
  tags: string[];
}
```

```typescript
// frontend/src/api.ts
import type { Note, NoteInput } from './types';

const BASE = '/api';

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let detail = `${r.status} ${r.statusText}`;
    try {
      const body = await r.json();
      if (body