import os
from datetime import datetime
from typing import Optional
import json

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from pydantic import BaseModel, Field, ConfigDict

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notebook.db")
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database model
class NoteModel(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    body = Column(Text)
    tags = Column(Text, default="[]")  # JSON array as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class TagListResponse(BaseModel):
    tags: list[str]

class NoteCreate(BaseModel):
    title: str
    body: str
    tags: list[str] = Field(default_factory=list)

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[list[str]] = None

class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# FastAPI app
app = FastAPI(title="Markdown Notebook")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/notes", response_model=NoteResponse)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = NoteModel(
        title=note.title,
        body=note.body,
        tags=json.dumps(note.tags),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return _format_note(db_note)

@app.get("/api/notes", response_model=list[NoteResponse])
def list_notes(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None)
):
    query = db.query(NoteModel)
    
    if search:
        search_lower = search.lower()
        # Filter by title, body, or tags (substring match)
        notes = []
        for note in query.all():
            if (search_lower in note.title.lower() or 
                search_lower in note.body.lower() or
                any(search_lower in t.lower() for t in json.loads(note.tags))):
                notes.append(note)
        results = sorted(notes, key=lambda n: n.updated_at, reverse=True)
    elif tag:
        # Filter by tag
        results = []
        for note in query.all():
            if tag in json.loads(note.tags):
                results.append(note)
        results = sorted(results, key=lambda n: n.updated_at, reverse=True)
    else:
        # All notes, most recently edited first
        results = query.order_by(NoteModel.updated_at.desc()).all()
    
    return [_format_note(note) for note in results]

@app.get("/api/tags", response_model=TagListResponse)
def get_all_tags(db: Session = Depends(get_db)):
    all_tags = set()
    for note in db.query(NoteModel).all():
        tags = json.loads(note.tags)
        all_tags.update(tags)
    
    return TagListResponse(tags=sorted(list(all_tags)))

@app.get("/api/notes/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _format_note(note)

@app.put("/api/notes/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_update: NoteUpdate, db: Session = Depends(get_db)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    if note_update.title is not None:
        db_note.title = note_update.title
    if note_update.body is not None:
        db_note.body = note_update.body
    if note_update.tags is not None:
        db_note.tags = json.dumps(note_update.tags)
    
    db_note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_note)
    return _format_note(db_note)

@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(NoteModel).filter(NoteModel.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(db_note)
    db.commit()
    return {"status": "deleted"}

def _format_note(db_note: NoteModel) -> NoteResponse:
    return NoteResponse(
        id=db_note.id,
        title=db_note.title,
        body=db_note.body,
        tags=json.loads(db_note.tags),
        created_at=db_note.created_at,
        updated_at=db_note.updated_at
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
