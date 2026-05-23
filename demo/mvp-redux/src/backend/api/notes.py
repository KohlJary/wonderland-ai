"""CRUD endpoints for notes.

GET /notes/{id} — fetch a single note by id
POST /notes — create a new note
GET /notes — list all notes (ordered by updated_at desc)
  - Optional query param: q={query} — search across title, body, tags (substring, case-insensitive)
  - Optional query param: tag={tagname} — filter by single tag
GET /notes — list all notes (ordered by updated_at desc)
PUT /notes/{id} — update a note
DELETE /notes/{id} — delete a note

All endpoints follow the contract defined in contract-note-01KSA5NS and contract-note-01KSA936.
"""

import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.models import Note

router = APIRouter()


class NoteCreate(BaseModel):
    """Request shape for POST /notes (create)."""

    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="")
    tags: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Request shape for PUT /notes/{id} (update)."""

    title: str = Field(min_length=1, max_length=255)
    body: str = Field(default="")
    tags: list[str] = Field(default_factory=list)


class NoteResponse(BaseModel):
    """Response shape for all CRUD endpoints (contract-note-01KSA5NS)."""

    id: int
    title: str
    body: str
    tags: list[str]
    created_at: str
    updated_at: str


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)) -> NoteResponse:
    """GET /notes/{id} — fetch a single note by id.

    Returns 200 with the note if found.
    Returns 404 if the note does not exist.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**note.to_dict())


@router.post("", response_model=NoteResponse, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)) -> NoteResponse:
    """POST /notes — create a new note.

    Request body includes title, body, and optional tags.
    Returns 201 Created with the created note including auto-generated id and timestamps.
    """
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    note = Note(
        title=payload.title,
        body=payload.body,
        tags=Note.tags_to_json(payload.tags),
        created_at=now,
        updated_at=now,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteResponse(**note.to_dict())


@router.get("", response_model=list[NoteResponse])
def list_notes(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Search query: substring match across title, body, tags"),
    tag: str | None = Query(None, description="Filter by single tag (case-sensitive)"),
) -> list[NoteResponse]:
    """GET /notes — list all notes.

    Query parameters (mutually exclusive):
    - q: search query (substring match, case-insensitive) across title, body, and tags.
      Results are ranked by relevance (exact tag match > title match > body match)
      with updated_at DESC as tiebreaker.
    - tag: filter by single tag (case-sensitive, exact match). Results ordered by updated_at DESC.

    If neither parameter is provided, returns all notes ordered by updated_at DESC.
    Empty results return 200 with [].
    """
    query = db.query(Note)

    if tag:
        # Tag filter: check if tag is in the tags JSON array (case-sensitive, exact match)
        notes = query.all()  # Fetch all, filter in Python (JSON array filtering is complex in SQLite)
        filtered = []
        for note in notes:
            try:
                tags_list = json.loads(note.tags) if note.tags else []
            except (json.JSONDecodeError, TypeError):
                tags_list = []
            if tag in tags_list:
                filtered.append(note)
        # Order by updated_at DESC
        filtered.sort(key=lambda n: n.updated_at or datetime.min, reverse=True)
        return [NoteResponse(**note.to_dict()) for note in filtered]

    if q:
        # Search query: substring match (case-insensitive) across title, body, tags
        # Ranking: exact tag match (highest), title match, body match
        # Tiebreaker: updated_at DESC
        query_lower = q.lower()
        notes = query.all()  # Fetch all for in-Python filtering and ranking

        results = []
        for note in notes:
            # Parse tags
            try:
                tags_list = json.loads(note.tags) if note.tags else []
            except (json.JSONDecodeError, TypeError):
                tags_list = []

            # Check for match and assign relevance score
            title_match = query_lower in note.title.lower()
            body_match = query_lower in note.body.lower()
            # Tag match: check if query matches any tag (case-insensitive substring)
            tag_matches = [tag for tag in tags_list if query_lower in tag.lower()]

            if title_match or body_match or tag_matches:
                # Relevance scoring: higher score = more relevant
                # Exact tag match: 1000, title match: 100, body match: 10
                relevance = 0
                if tag_matches:
                    relevance += 1000
                if title_match:
                    relevance += 100
                if body_match:
                    relevance += 10

                results.append((note, relevance))

        # Sort by relevance (descending), then by updated_at (descending)
        results.sort(
            key=lambda x: (x[1], x[0].updated_at or datetime.min),
            reverse=True
        )
        return [NoteResponse(**note.to_dict()) for note, _ in results]

    # No filter: return all notes ordered by updated_at DESC
    notes = query.order_by(Note.updated_at.desc()).all()
    return [NoteResponse(**note.to_dict()) for note in notes]


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)
) -> NoteResponse:
    """PUT /notes/{id} — update a note.

    Request body includes title, body, and optional tags.
    updated_at is auto-updated by the server (via SQLAlchemy onupdate).
    Returns 200 with the updated note if found.
    Returns 404 if the note does not exist.
    """
    from datetime import datetime, timezone
    
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.title = payload.title
    note.body = payload.body
    note.tags = Note.tags_to_json(payload.tags)
    note.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(note)
    return NoteResponse(**note.to_dict())


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    """DELETE /notes/{id} — delete a note.

    Returns 204 No Content if found and deleted.
    Returns 404 if the note does not exist.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    db.delete(note)
    db.commit()
