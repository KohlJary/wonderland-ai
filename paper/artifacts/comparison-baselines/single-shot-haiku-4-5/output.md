# Personal Markdown Notebook Web App

I'll build a complete fullstack markdown notebook app with Python/FastAPI backend and React/TypeScript frontend.

## Project Structure

```
markdown-notebook/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── api.py
│   ├── pyproject.toml
│   └── notes.db (created at runtime)
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── NoteEditor.tsx
│   │   │   ├── NotePreview.tsx
│   │   │   ├── NoteList.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── TagFilter.tsx
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── index.html
├── tests/
│   ├── test_api.py
│   └── __init__.py
└── README.md
```

---

## Backend Files

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router
from database import init_db

app = FastAPI(title="Markdown Notebook")

# Initialize database on startup
init_db()

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```python
# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationship between notes and tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE")),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE")),
)

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": [tag.name for tag in self.tags] if hasattr(self, "tags") else [],
        }

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
```

```python
# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, relationship
from models import Base, Note, Tag, note_tags

DATABASE_URL = "sqlite:///./notes.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add relationship to Note model after SessionLocal is created
Note.tags = relationship(
    Tag,
    secondary=note_tags,
    backref="notes",
)
```

```python
# backend/api.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from datetime import datetime
from database import get_db
from models import Note, Tag, note_tags
from typing import List, Optional

router = APIRouter(prefix="/api", tags=["notes"])

# ============ Note Endpoints ============

@router.post("/notes")
def create_note(
    title: str = Query(...),
    body: str = Query(...),
    tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """Create a new note with optional tags."""
    # Create note
    note = Note(title=title, body=body)
    db.add(note)
    db.flush()

    # Attach tags
    if tags:
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
            note.tags.append(tag)

    db.commit()
    db.refresh(note)
    return note.to_dict()

@router.get("/notes")
def list_notes(
    db: Session = Depends(get_db),
):
    """List all notes, sorted by most recently updated first."""
    notes = db.query(Note).order_by(desc(Note.updated_at)).all()
    return [note.to_dict() for note in notes]

@router.get("/notes/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a single note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note.to_dict()

@router.put("/notes/{note_id}")
def update_note(
    note_id: int,
    title: str = Query(...),
    body: str = Query(...),
    tags: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
):
    """Update an existing note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = title
    note.body = body
    note.updated_at = datetime.utcnow()

    # Clear existing tags
    note.tags.clear()

    # Add new tags
    if tags:
        for tag_name in tags:
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
            note.tags.append(tag)

    db.commit()
    db.refresh(note)
    return note.to_dict()

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"success": True}

# ============ Search Endpoints ============

@router.get("/notes/search")
def search_notes(
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    """Search notes by title, body, or tags."""
    search_term = f"%{q}%"
    notes = db.query(Note).filter(
        or_(
            Note.title.ilike(search_term),
            Note.body.ilike(search_term),
            Note.tags.any(Tag.name.ilike(search_term)),
        )
    ).order_by(desc(Note.updated_at)).all()
    return [note.to_dict() for note in notes]

# ============ Tag Endpoints ============

@router.get("/tags")
def list_tags(db: Session = Depends(get_db)):
    """List all tags used in notes."""
    tags = db.query(Tag).order_by(Tag.name).all()
    return [tag.to_dict() for tag in tags]

@router.get("/tags/{tag_name}/notes")
def get_notes_by_tag(
    tag_name: str,
    db: Session = Depends(get_db),
):
    """Get all notes with a specific tag."""
    tag = db.query(Tag).filter(Tag.name.ilike(tag_name)).first()
    if not tag:
        return []
    notes = db.query(Note).filter(Note.tags.contains(tag)).order_by(desc(Note.updated_at)).all()
    return [note.to_dict() for note in notes]
```

```toml
# backend/pyproject.toml
[project]
name = "markdown-notebook-backend"
version = "0.1.0"
description = "Personal markdown notebook backend"
requires-python = ">=3.9"
dependencies = [
    "fastapi==0.104.1",
    "uvicorn[standard]==0.24.0",
    "sqlalchemy==2.0.23",
    "pydantic==2.5.0",
]

[project.optional-dependencies]
dev = [
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1",
    "httpx==0.25.1",
]
```

---

## Frontend Files

```typescript
// frontend/src/types/index.ts
export interface Note {
  id: number;
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
  tags: string[];
}

export interface Tag {
  id: number;
  name: string;
}
```

```typescript
// frontend/src/api/client.ts
const API_BASE = "/api";

export const apiClient = {
  // Notes
  async createNote(title: string, body: string, tags: string[]) {
    const params = new URLSearchParams({ title, body });
    tags.forEach((tag) => params.append("tags", tag));

    const response = await fetch(`${API_BASE}/notes`, {
      method: "POST",
      body: params,
    });
    if (!response.ok) throw new Error("Failed to create note");
    return response.json();
  },

  async listNotes() {
    const response = await fetch(`${API_BASE}/notes`);
    if (!response.ok) throw new Error("Failed to fetch notes");
    return response.json();
  },

  async getNote(id: number) {
    const response = await fetch(`${API_BASE}/notes/${id}`);
    if (!response.ok) throw new Error("Failed to fetch note");
    return response.json();
  },

  async updateNote(id: number, title: string, body: string, tags: string[]) {
    const params = new URLSearchParams({ title, body });
    tags.forEach((tag) => params.append("tags", tag));

    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: "PUT",
      body: params,
    });
    if (!response.ok) throw new Error("Failed to update note");
    return response.json();
  },

  async deleteNote(id: number) {
    const response = await fetch(`${API_BASE}/notes/${id}`, {
      method: "DELETE",
    });
    if (!response.ok) throw new Error("Failed to delete note");
    return response.json();
  },

  async searchNotes(query: string) {
    const response = await fetch(`${API_BASE}/notes/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error("Failed to search notes");
    return response.json();
  },

  // Tags
  async listTags() {
    const response = await fetch(`${API_BASE}/tags`);
    if (!response.ok) throw new Error("Failed to fetch tags");
    return response.json();
  },

  async getNotesByTag(tagName: string) {
    const response = await fetch(
      `${API_BASE}/tags/${encodeURIComponent(tagName)}/notes`
    );
    if (!response.ok) throw new Error("Failed to fetch notes by tag");
    return response.json();
  },
};
```

```typescript
// frontend/src/components/SearchBar.tsx
import React, { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
  const [query, setQuery] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    onSearch(value);
  };

  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="Search notes..."
        value={query}
        onChange={handleChange}
        className="search-input"
      />
    </div>
  );
};
```

```typescript
// frontend/src/components/TagFilter.tsx
import React from "react";

interface TagFilterProps {
  tags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
}

export const TagFilter: React.FC<TagFilterProps> = ({
  tags,
  selectedTag,
  onSelectTag,
}) => {
  return (
    <div className="tag-filter">
      <div className="tag-filter-header">Tags</div>
      <button
        className={`tag-button ${selectedTag === null ? "active" : ""}`}
        onClick={() => onSelectTag(null)}
      >
        All
      </button>
      {tags.map((tag) => (
        <button
          key={tag}
          className={`tag-button ${selectedTag === tag ? "active" : ""}`}
          onClick={() => onSelectTag(tag)}
        >
          {tag}
        </button>
      ))}
    </div>
  );
};
```

```typescript
// frontend/src/components/NoteList.tsx
import React from "react";
import { Note } from "../types";

interface NoteListProps {
  notes: Note[];
  selectedNoteId: number | null;
  onSelectNote: (id: number) => void;
  onDeleteNote: (id: number) => void;
}

export const NoteList: React.FC<NoteListProps> = ({
  notes,
  selectedNoteId,
  onSelectNote,
  onDeleteNote,
}) => {
  return (
    <div className="note-list">
      <div className="note-list-header">Notes ({notes.length})</div>
      {notes.length === 0 ? (
        <div className="no-notes">No notes found. Create one to get started!</div>
      ) : (
        notes.map((note) => (
          <div
            key={note.id}
            className={`note-item ${selectedNoteId === note.id ? "active" : ""}`}
            onClick={() => onSelectNote(note.id)}
          >
            <div className="note-item-header">
              <div className="note-item-title">{note.title}</div>
              <button
                className="delete-button"
                onClick={(e) => {
                  e.stopPropagation();
                  if (
                    window.confirm(
                      "Are you sure you want to delete this note?"
                    )
                  ) {
                    onDeleteNote(note.id);
                  }
                }}
                title="Delete note"
              >
                ✕
              </button>
            </div>
            <div className="note-item-preview">
              {note.body.substring(0, 100)}
              {note.body.length > 100 ? "..." : ""}
            </div>
            {note.tags.length > 0 && (
              <div className="note-item-tags">
                {note.tags.map((tag) => (
                  <span key={tag} className="tag-badge">
                    {tag}
                  </span>
                ))}
              </div>
            )}
            <div className="note-item-date">
              {new Date(note.updated_at).toLocaleDateString()}
            </div>
          </div>
        ))
      )}
    </div>
  );
};
```

```typescript
// frontend/src/components/NoteEditor.tsx
import React, { useState, useEffect } from "react";
import { Note } from "../types";

interface NoteEditorProps {
  note: Note | null;
  onSave: (title: string, body: string, tags: string[]) => void;
  onNew: () => void;
}

export const NoteEditor: React.FC<NoteEditorProps> = ({
  note,
  onSave,
  onNew,
}) => {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [tags, setTags] = useState("");
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (note) {
      setTitle(note.title);
      setBody(note.body);
      setTags(note.tags.join(", "));
      setIsDirty(false);
    }
  }, [note]);

  const handleSave = () => {
    const tagList = tags
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    onSave(title, body, tagList);
    setIsDirty(false);
  };

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTitle(e.target.value);
    setIsDirty(true);
  };

  const handleBodyChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setBody(e.target.value);
    setIsDirty(true);
  };

  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTags(e.target.value);
    setIsDirty(true);
  };

  return (
    <div className="note-editor">
      <div className="editor-header">
        <button onClick={onNew} className="new-button">
          ➕ New Note
        </button>
        <button
          onClick={handleSave}
          className="save-button"
          disabled={!isDirty && note !== null}
        >
          💾 Save
        </button>
      </div>

      <input
        type="text"
        placeholder="Note title..."
        value={title}
        onChange={handleTitleChange}
        className="editor-title"
      />

      <input
        type="text"
        placeholder="Tags (comma-separated)..."
        value={tags}
        onChange={handleTagsChange}
        className="editor-tags"
      />

      <textarea
        placeholder="Write your markdown here..."
        value={body}
        onChange={handleBodyChange}
        className="editor-body"
      />
    </div>
  );
};
```

```typescript
// frontend/src/components/NotePreview.tsx
import React from "react";
import ReactMarkdown from "react-markdown";
import { Note } from "../types";

interface NotePreviewProps {
  note: Note | null;
}

export const NotePreview: React.FC<NotePreviewProps> = ({ note }) => {
  return (
    <div className="note-preview">
      <div className="preview-header">Preview</div>
      {note ? (
        <div className="preview-content">
          <h1>{note.title}</h1>
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1>{children}</h1>,
              h2: ({ children }) => <h2>{children}</h2>,
              h3: ({ children }) => <h3>{children}</h3>,
              h4: ({ children }) => <h4>{children}</h4>,
              h5: ({ children }) => <h5>{children}</h5>,
              h6: ({ children }) => <h6>{children}</h6>,
              p: ({ children }) => <p>{children}</p>,
              blockquote: ({ children }) => <blockquote>{children}</blockquote>,
              ul: ({ children }) => <ul>{children}</ul>,
              ol: ({ children }) => <ol>{children}</ol>,
              li: ({ children }) => <li>{children}</li>,
              code: ({ inline, children }) =>
                inline ? (
                  <code className="inline-code">{children}</code>
                ) : (
                  <pre>
                    <code>{children}</code>
                  </pre>
                ),
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
              img: ({ src, alt }) => (
                <img src={src} alt={alt} style={{ maxWidth: "100%" }} />
              ),
            }}
          >
            {note.body}
          </ReactMarkdown>
        </div>
      ) : (
        <div className="no-preview">Select a note to preview</div>
      )}
    </div>
  );
};
```

```typescript
// frontend/src/App.tsx
import React, { useState, useEffect } from "react";
import { Note } from "./types";
import { apiClient } from "./api/client";
import { NoteList } from "./components/NoteList";
import { NoteEditor } from "./components/NoteEditor";
import { NotePreview } from "./components/NotePreview";
import { SearchBar } from "./components/SearchBar";
import { TagFilter } from "./components/TagFilter";
import "./App.css";

function App() {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selectedNoteId, setSelectedNoteId] = useState<number | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const selectedNote = notes.find((n) => n.id === selectedNoteId) || null;

  // Load initial data
  useEffect(() => {
    loadNotes();
    loadTags();
  }, []);

  const loadNotes = async () => {
    try {
      setLoading(true);
      const data = await apiClient.listNotes();
      setNotes(data);
      if (data.length > 0 && selectedNoteId === null) {
        setSelectedNoteId(data[0].id);
      }
    } catch (error) {
      console.error("Failed to load notes:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadTags = async () => {
    try {
      const data = await apiClient.listTags();
      setTags(data.map((t: any) => t.name).sort());
    } catch (error) {
      console.error("Failed to load tags:", error);
    }
  };

  const handleSearch = async (query: string) => {
    setSearchQuery(query);
    setSelectedTag(null);

    if (query.trim() === "") {
      loadNotes();
    } else {
      try {
        const data = await apiClient.searchNotes(query);
        setNotes(data);
      } catch (error) {
        console.error("Search failed:", error);
      }
    }
  };

  const handleTagSelect = async (tag: string | null) => {
    setSelectedTag(tag);
    setSearchQuery("");

    if (tag === null) {
      loadNotes();
    } else {
      try {
        const data = await apiClient.getNotesByTag(tag);
        setNotes(data);
      } catch (error) {
        console.error("Failed to load notes by tag:", error);
      }
    }
  };

  const handleSaveNote = async (
    title: string,
    body: string,
    newTags: string[]
  ) => {
    if (!title.trim()) {
      alert("Note title cannot be empty");
      return;
    }

    try {
      if (selectedNote) {
        // Update existing note
        const updated = await apiClient.updateNote(
          selectedNote.id,
          title,
          body,
          newTags
        );
        setNotes(
          notes.map((n) => (n.id === updated.id ? updated : n))
        );
      } else {
        // Create new note
        const created = await apiClient.createNote(title, body, newTags);
        setNotes([created, ...notes]);
        setSelectedNoteId(created.id);
      }
      loadTags();
    } catch (error) {
      console.error("Failed to save note:", error);
      alert("Failed to save note");
    }
  };

  const handleDeleteNote = async (id: number) => {
    try {
      await apiClient.deleteNote(id);
      const newNotes = notes.filter((n) => n.id !== id);
      setNotes(newNotes);
      if (selectedNoteId === id) {
        setSelectedNoteId(newNotes.length > 0 ? newNotes[0].id : null);
      }
      loadTags();
    } catch (error) {
      console.error("Failed to delete note:", error);
      alert("Failed to delete note");
    }
  };

  const handleNewNote = () => {
    setSelectedNoteId(null);
    setSearchQuery("");
    setSelectedTag(null);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📝 Markdown Notebook</h1>
      </header>

      <div className="app-container">
        <aside className="sidebar">
          <SearchBar onSearch={handleSearch} />
          <TagFilter
            tags={tags}
            selectedTag={selectedTag}
            onSelectTag={handleTagSelect}
          />
          <NoteList
            notes={notes}
            selectedNoteId={selectedNoteId}
            onSelectNote={setSelectedNoteId}
            onDeleteNote={handleDeleteNote}
          />
        </aside>

        <main className="main-content">
          <div className="editor-pane">
            <NoteEditor
              note={selectedNote}
              onSave={handleSaveNote}
              onNew={handleNewNote}
            />
          </div>

          <div className="preview-pane">
            <NotePreview note={selectedNote} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
```

```css
/* frontend/src/App.css */
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.app-container {
  display: flex;
  flex: 1;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.search-bar {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  background: white;
  transition: border-color 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.tag-filter {
  background: white;
  padding: 12px;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.tag-filter-header {
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 8px;
}

.tag-button {
  display: block;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  margin-bottom: 4px;
  border: none;
  background: #f9f9f9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
  color: #333;
}

.tag-button:hover {
  background: #f0f0f0;
}

.tag-button.active {
  background: #667eea;
  color: white;
  font-weight: 500;
}

.note-list {
  flex: 1;
  background: white;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.note-list-header {
  padding: 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: #666;
  border-bottom: 1px solid #eee;
}

.note-list {
  overflow-y: auto;
}

.no-notes {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.note-item {
  padding: 12px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background-color 0.2s;
}

.note-item:hover {
  background-color: #f9f9f9;
}

.note-item.active {
  background-color: #f0f0f7;
  border-left: 3px solid #667eea;
  padding-