from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from backend.database import get_db, Base, engine
from backend.models import Note, Tag, note_tags
from backend.schemas import NoteCreate, NoteUpdate, NoteResponse

app = FastAPI(title="Markdown Notebook")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize database lazily - will be called once on startup
_db_initialized = False

def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        Base.metadata.create_all(bind=engine)
        _db_initialized = True


@app.get("/api/health")
async def health():
    ensure_db_initialized()
    return {"status": "ok"}


@app.post("/api/notes", response_model=NoteResponse)
async def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """Create a new note with tags."""
    db_note = Note(title=note.title, body=note.body)

    # Handle tags: get existing or create new
    for tag_name in note.tags:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
        db_note.tags.append(tag)

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@app.get("/api/notes", response_model=list[NoteResponse])
async def list_notes(
    tag: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """List all notes, optionally filtered by tag and/or search term."""
    query = db.query(Note)

    # Filter by tag if provided
    if tag:
        query = query.join(Note.tags).filter(Tag.name == tag)

    # Filter by search term (title, body, or tag names)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Note.title.ilike(search_term),
                Note.body.ilike(search_term),
                Note.tags.any(Tag.name.ilike(search_term)),
            )
        )

    # Sort by updated_at descending (most recent first)
    query = query.order_by(desc(Note.updated_at))
    notes = query.all()
    return notes


@app.get("/api/notes/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@app.put("/api/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = note_update.title
    note.body = note_update.body

    # Update tags
    note.tags.clear()
    for tag_name in note_update.tags:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
        note.tags.append(tag)

    db.commit()
    db.refresh(note)
    return note


@app.delete("/api/notes/{note_id}")
async def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Delete a note."""
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/tags")
async def list_tags(db: Session = Depends(get_db)):
    """List all tags currently in use."""
    tags = db.query(Tag).order_by(Tag.name).all()
    return [{"id": tag.id, "name": tag.name} for tag in tags]
