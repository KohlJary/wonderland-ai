"""Complete CRUD endpoints for notes and tag associations.

Contracts (from contract-note-01KRXRTT, 01KRXRVG, 01KRXRVT, 01KRXRWW, contract-note-search-response-envelope-rapid-rediscovery):
- POST /api/notes: request {title: str, body?: str, tag_names?: str[]}
                   response 201 {id, title, body, tag_names: str[], tag_ids: int[], created_at, updated_at}
- GET /api/notes: response 200 [{id, title, body, tag_names, tag_ids, created_at, updated_at}] (reverse chronological)
- GET /api/notes/{id}: response 200 {id, title, body, tag_names, tag_ids, created_at, updated_at}
                       returns 404 if not found
- PUT /api/notes/{id}: request {title?: str, body?: str, tag_names?: str[]}
                      response 200 {id, title, body, tag_names, tag_ids, created_at, updated_at}
                      returns 404 if not found
- DELETE /api/notes/{id}: response 204 (no content)
                         returns 404 if not found
- POST /api/notes/{id}/tags: request {tag_name: str}
                            response 200 {id, title, body, tag_names, tag_ids, created_at, updated_at}
                            auto-creates tag if missing
                            returns 404 if note not found
- DELETE /api/notes/{id}/tags/{tag_id}: response 204 (no content)
                                       returns 404 if note or tag not found
- GET /api/search: query params {q?: str, tags?: str, page?: int, page_size?: int}
                   response 200 {results: [{id, title, body_preview (100 chars), tag_names, tag_ids, created_at, updated_at}], 
                                          total_results: int, page: int, page_size: int, has_more: bool}
                   case-insensitive substring match on title and body
                   filters by tag names if provided (comma-separated)
                   pagination support with default page_size 20, 1-indexed pages
                   body_preview optimized to 100 chars for rapid-rediscovery scanning per v1.1 contract
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session
import json
import hashlib

from src.backend.db import get_db
from src.backend.models import Note, Tag, AuditLog, compute_revision_id

router = APIRouter()


def _record_audit_log(
    db: Session, 
    note_id: int, 
    title: str, 
    body: str, 
    tag_ids: list[int], 
    updated_at: str,
    collision_detected: bool = False,
    conflicting_revision_id: str | None = None
) -> str:
    """Record an immutable audit log entry for a note save or save attempt.
    
    Computes revision_id and state_hash, creates an AuditLog row.
    Called after every save (success) or collision (409) to maintain complete audit trail.
    
    Args:
        db: SQLAlchemy session
        note_id: the note being saved
        title: note title (or attempted title on collision)
        body: note body (or attempted body on collision)
        tag_ids: sorted list of tag IDs (or attempted tags on collision)
        updated_at: ISO8601 timestamp of the note's updated_at (server-side, unchanged on collision)
        collision_detected: bool, true if this save was rejected due to If-Match mismatch
        conflicting_revision_id: if collision_detected=true, the server's current revision_id at conflict time
    
    Returns:
        revision_id (opaque SHA256 hex digest), to be returned in the save response
    
    Invariant: audit log entries are immutable (never updated or deleted)
    """
    # Compute revision_id from current state (or attempted state on collision)
    revision_id = compute_revision_id(title, body, tag_ids, updated_at)
    
    # Save state snapshot: {title, body, tag_ids} as JSON for forensic reconstruction
    saved_state = {
        "title": title,
        "body": body,
        "tag_ids": sorted(tag_ids),
    }
    saved_state_json = json.dumps(saved_state, separators=(",", ":"))
    
    # Compute state_hash for tamper detection
    state_hash_input = f"{note_id}{updated_at}{saved_state_json}"
    state_hash = hashlib.sha256(state_hash_input.encode("utf-8")).hexdigest()
    
    # Create and persist audit log entry
    log_entry = AuditLog(
        note_id=note_id,
        user_id=None,  # v1: single-user, no user tracking
        saved_state_json=saved_state_json,
        revision_id=revision_id,
        state_hash=state_hash,
        collision_detected=collision_detected,
        conflicting_revision_id=conflicting_revision_id,
    )
    db.add(log_entry)
    db.flush()  # Ensure it's persisted before returning
    
    return revision_id


class NoteCreate(BaseModel):
    """Request body for POST /api/notes.
    
    Invariants enforced:
    - title: required, non-empty string (1-255 chars)
    - body: optional string, defaults to None (stored as "" in database)
    - tag_names: optional array of tag name strings, defaults to []
    """
    title: str = Field(min_length=1, max_length=255)
    body: str | None = Field(default=None, max_length=16384)
    tag_names: list[str] = Field(default_factory=list)


class NoteUpdate(BaseModel):
    """Request body for PUT /api/notes/{id}.
    
    All fields optional; only provided fields are updated.
    """
    title: str | None = Field(default=None, min_length=1, max_length=255)
    body: str | None = Field(default=None, max_length=16384)
    tag_names: list[str] | None = Field(default=None)


class TagCreate(BaseModel):
    """Request body for POST /api/notes/{id}/tags."""
    tag_name: str = Field(min_length=1, max_length=100)


class TagResponse(BaseModel):
    """Tag representation in response bodies."""
    id: int
    name: str


class NoteResponse(BaseModel):
    """Response body for GET /api/notes/{id}, POST /api/notes, PUT /api/notes/{id}.
    
    All timestamps in ISO8601 format with timezone (UTC).
    Tags returned as both names and IDs per contract-note-004.
    revision_id is an opaque SHA256 hash of the note state, returned for collision detection
    per contract-note-01KRY0B8. Client caches this and sends as If-Match header on next update.
    
    Contract reference: contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side)
    """
    id: int
    title: str
    body: str
    tag_names: list[str]
    tag_ids: list[int]
    created_at: str
    updated_at: str
    revision_id: str  # Opaque SHA256 hash of [title, body, sorted_tag_ids, updated_at]


class SearchResultNote(BaseModel):
    """Search result representation (different from full NoteResponse).
    
    Per contract-note-search-response-envelope-rapid-rediscovery (agreed search-api/v1.1):
    - Returns body_preview (first 100 chars) instead of full body
    - Includes all other fields from NoteResponse
    - 100-char preview optimized for Kohl's rapid-rediscovery scanning workflow
    - Includes revision_id for consistency with full NoteResponse
    
    Invariant: body_preview is always <= 100 chars (truncated at 100).
    """
    id: int
    title: str
    body_preview: str  # First 100 chars of body, truncated for rapid-rediscovery scanning
    tag_names: list[str]
    tag_ids: list[int]
    created_at: str
    updated_at: str
    revision_id: str


class SearchResponse(BaseModel):
    """Response body for GET /api/search.
    
    Paginated results with total_results count and has_more flag.
    Per contract-note-search-response-envelope-rapid-rediscovery (agreed search-api/v1.1):
    - total_results: total count of matching notes (across all pages)
    - page: current page number (1-indexed per contract)
    - page_size: items per page
    - results: array of notes matching search criteria (with body_preview truncated to 100 chars)
    - has_more: true if there are more results beyond current page
    """
    results: list[SearchResultNote]
    total_results: int
    page: int
    page_size: int
    has_more: bool


def _escape_like_pattern(s: str) -> str:
    """Escape SQL LIKE metacharacters (%, _) so they are treated as literals.
    
    CRITICAL: The pattern returned by this function MUST be used with a
    LIKE comparison that specifies escape='\\' (double-backslash in Python string).
    If the escape parameter is omitted, the escaping is ineffective and user input
    containing % or _ will be treated as SQL wildcards — this is a correctness bug
    and a security issue.
    
    DO NOT call this function and then use .ilike() without escape='\\'.
    Use the _safe_ilike() helper instead to enforce this contract at the call site.
    
    In SQLite LIKE:
    - % matches zero or more characters (wildcard)
    - _ matches exactly one character (wildcard)
    - \ is the escape character (we use \ to escape % and _)
    
    This function escapes % and _ so they match literally.
    Used for search queries to ensure user input doesn't accidentally use LIKE wildcards.
    """
    # Replace % with \%, _ with \_
    escaped = s.replace("\\", "\\\\")  # Escape existing backslashes first
    escaped = escaped.replace("%", "\\%")
    escaped = escaped.replace("_", "\\_")
    return escaped


def _safe_ilike(column, pattern: str):
    """Helper to apply LIKE comparison with automatic escape character enforcement.
    
    Wraps SQLAlchemy's .ilike() to enforce the contract that escaped patterns
    (from _escape_like_pattern()) MUST be used with escape='\\'.
    
    This prevents the bug where a caller forgets to include escape="\\" in the
    ilike() call, causing % and _ in user input to become wildcards.
    
    Args:
        column: SQLAlchemy column to filter
        pattern: pattern to match (typically from _escape_like_pattern() or wrapped with %)
    
    Returns:
        SQLAlchemy ColumnElement with escape='\\' enforced
    
    Example:
        # Before (bug-prone):
        q = q.filter(Note.title.ilike(f"%{_escape_like_pattern(q)}%", escape="\\"))
        
        # After (safe):
        q = q.filter(_safe_ilike(Note.title, f"%{_escape_like_pattern(q)}%"))
    """
    return column.ilike(pattern, escape="\\")


def _normalize_and_validate_tag_names(tag_names: list[str]) -> list[str]:
    """Normalize and validate tag names per contract-note-01KRXYD0.
    
    Validation rules:
    1. Strip leading/trailing whitespace from each tag name
    2. Reject (raise HTTPException 400) any tag that after stripping is empty or whitespace-only
    3. Deduplicate by exact name match (case-sensitive)
    4. Return normalized, unique tag names
    
    Raises HTTPException 400 if any tag name is invalid.
    """
    normalized = []
    seen = set()
    
    for tag_name in tag_names:
        # Strip whitespace
        stripped = tag_name.strip()
        
        # Reject if empty after stripping
        if not stripped:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag names cannot be empty or whitespace-only"
            )
        
        # Deduplicate (case-sensitive)
        if stripped not in seen:
            normalized.append(stripped)
            seen.add(stripped)
    
    return normalized


def _associate_tags(db: Session, note: Note, tag_names: list[str]) -> None:
    """Associate note with tags by name, auto-creating tags if missing.
    
    Clears existing tag associations and creates new ones.
    Normalizes and validates tag_names (strips whitespace, rejects empty, deduplicates).
    All tag_names must be non-empty and non-whitespace after normalization.
    Single transaction: all-or-nothing.
    """
    # Clear existing associations
    note.tags.clear()
    
    # Normalize and validate tag names
    normalized_tag_names = _normalize_and_validate_tag_names(tag_names)
    
    # For each tag name, find or create the tag
    for tag_name in normalized_tag_names:
        tag = db.query(Tag).filter(Tag.name == tag_name).first()
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()  # Ensure tag is created before association
        note.tags.append(tag)


@router.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    payload: NoteCreate, db: Session = Depends(get_db)
) -> NoteResponse:
    """Create a new note with title, optional body, optional tags.
    
    Validation:
    - title must be non-empty (1-255 chars)
    - body optional, max 16384 chars (None in request becomes "" in storage)
    - tags optional, auto-created if missing
    
    Audit trail: Creates an immutable log entry with full-state snapshot, revision_id, and state_hash.
    Collision detection: Returns revision_id (opaque hash) for client to cache and use on subsequent updates.
    
    Returns 201 with created note (id, timestamps, full content, revision_id).
    
    Contract reference: contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side)
    """
    note = Note(title=payload.title, body=payload.body or "")
    db.add(note)
    db.flush()  # Ensure note is assigned an id before associating tags
    
    # Associate tags (auto-create if missing)
    if payload.tag_names:
        _associate_tags(db, note, payload.tag_names)
    
    db.commit()
    db.refresh(note)  # Refresh to get server-assigned timestamps
    
    # Compute and record audit trail
    tag_ids = [tag.id for tag in note.tags]
    revision_id = _record_audit_log(db, note.id, note.title, note.body, tag_ids, note.updated_at.isoformat())
    
    db.commit()
    
    # Build response with revision_id
    response_dict = note.to_dict()
    response_dict["revision_id"] = revision_id
    return NoteResponse(**response_dict)


@router.get("/notes", response_model=list[NoteResponse])
def list_notes(db: Session = Depends(get_db)) -> list[NoteResponse]:
    """Retrieve all notes in reverse chronological order (newest first).
    
    Secondary sort by id DESC for deterministic ordering when timestamps are equal.
    
    Returns 200 with array of notes, each with computed revision_id for boot-time
    merge reconciliation per contract-note-01KRY0B8 and ticket-064.
    
    Frontend uses revision_id to reconcile persisted notes with localStorage keystroke
    buffers on page reload: compares revision_id to detect stale localStorage entries
    and prompt user for merge strategy.
    """
    notes = db.query(Note).order_by(Note.updated_at.desc(), Note.id.desc()).all()
    
    results = []
    for note in notes:
        note_dict = note.to_dict()
        
        # Compute revision_id for this note (same as POST/PUT returns)
        tag_ids = [tag.id for tag in note.tags]
        revision_id = compute_revision_id(
            note.title,
            note.body,
            tag_ids,
            note_dict["updated_at"]  # Use ISO8601 string from to_dict()
        )
        
        note_dict["revision_id"] = revision_id
        results.append(NoteResponse(**note_dict))
    
    return results


@router.get("/notes/{note_id}", response_model=NoteResponse)
def read_note(note_id: int, db: Session = Depends(get_db)) -> NoteResponse:
    """Retrieve a note by id.
    
    Returns revision_id (opaque hash of current state) for collision detection on subsequent updates.
    Collision detection: Client caches revision_id from this response and sends as If-Match header
    on PUT. If mismatch, server returns 409 Conflict.
    
    Returns 200 with full note if found.
    Returns 404 if note does not exist.
    
    Contract reference: contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side)
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    # Compute current revision_id
    response_dict = note.to_dict()
    tag_ids = [tag.id for tag in note.tags]
    revision_id = compute_revision_id(note.title, note.body, tag_ids, note.updated_at.isoformat())
    response_dict["revision_id"] = revision_id
    
    return NoteResponse(**response_dict)


@router.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    if_match: str | None = Header(default=None),
    db: Session = Depends(get_db)
) -> NoteResponse:
    """Update a note's title, body, and/or tags with optimistic locking via If-Match header.
    
    Collision detection:
    - Client sends If-Match: <cached_revision_id> header (from prior GET or POST response).
    - Server computes current revision_id and compares.
    - If match: update proceeds (200).
    - If mismatch: returns 409 Conflict with {error: 'ConflictError', server_revision_id, server_state}.
    - If header is absent: update proceeds (backward-compatible for v1 single-user scope).
    
    All fields optional; only provided fields are updated.
    Tag association is atomic: if tag_names provided, replaces all tags.
    
    Audit trail: Records immutable log entry with full-state snapshot, revision_id, and state_hash.
    
    Returns 200 with updated note and new revision_id.
    Returns 404 if note does not exist.
    Returns 409 Conflict if If-Match header is provided and does not match current revision.
    
    Contract reference: contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side)
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    # Compute current revision_id before any updates
    tag_ids_before = [tag.id for tag in note.tags]
    current_revision_id = compute_revision_id(note.title, note.body, tag_ids_before, note.updated_at.isoformat())
    
    # Collision detection: validate If-Match header if provided
    if if_match is not None and if_match != current_revision_id:
        # Log the collision attempt in audit trail before rejecting
        attempted_title = payload.title if payload.title is not None else note.title
        attempted_body = payload.body if payload.body is not None else note.body
        
        # For tag_ids on collision: if payload has tag_names, resolve to tag_ids
        # Otherwise use current note's tags
        if payload.tag_names is not None:
            # Normalize tag names
            normalized_tag_names = _normalize_and_validate_tag_names(payload.tag_names)
            # Resolve to tag IDs (creating tags if needed)
            attempted_tag_ids = []
            for tag_name in normalized_tag_names:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    db.flush()
                attempted_tag_ids.append(tag.id)
        else:
            attempted_tag_ids = [tag.id for tag in note.tags]
        
        # Record the attempted save in audit trail
        _record_audit_log(
            db, 
            note.id, 
            attempted_title, 
            attempted_body, 
            attempted_tag_ids, 
            note.updated_at.isoformat(),
            collision_detected=True,
            conflicting_revision_id=current_revision_id
        )
        db.commit()  # Ensure audit log is persisted
        
        # Compute the state to return in the conflict response
        tag_ids_current = [tag.id for tag in note.tags]
        server_revision_id = compute_revision_id(note.title, note.body, tag_ids_current, note.updated_at.isoformat())
        server_state = note.to_dict()
        server_state["revision_id"] = server_revision_id
        
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "ConflictError",
                "message": "Note has been updated since you last synced. Please review the server version and retry.",
                "server_revision_id": server_revision_id,
                "server_state": server_state,
            }
        )
    
    # Update title if provided
    if payload.title is not None:
        note.title = payload.title
    
    # Update body if provided
    if payload.body is not None:
        note.body = payload.body
    
    # Update tags if provided
    if payload.tag_names is not None:
        _associate_tags(db, note, payload.tag_names)
    
    db.commit()
    db.refresh(note)  # Refresh to get updated timestamp
    
    # Compute and record audit trail
    tag_ids_after = [tag.id for tag in note.tags]
    revision_id = _record_audit_log(db, note.id, note.title, note.body, tag_ids_after, note.updated_at.isoformat())
    
    db.commit()
    
    # Build response with new revision_id
    response_dict = note.to_dict()
    response_dict["revision_id"] = revision_id
    return NoteResponse(**response_dict)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a note by id.
    
    Returns 204 (no content) on success.
    Returns 404 if note does not exist.
    
    Cascade: note_tags associations are automatically deleted.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    db.delete(note)
    db.commit()


@router.post("/notes/{note_id}/tags", response_model=NoteResponse)
def associate_tag(
    note_id: int, payload: TagCreate, db: Session = Depends(get_db)
) -> NoteResponse:
    """Associate a tag with a note (auto-create tag if missing).
    
    If tag_name doesn't exist, creates it.
    If tag is already associated with the note, no-op (idempotent).
    
    Validation: tag_name is normalized (whitespace stripped) and must not be empty
    after stripping (per contract-note-01KRXYD0).
    
    Returns 200 with updated note.
    Returns 400 if tag_name is invalid (empty or whitespace-only after stripping).
    Returns 404 if note does not exist.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    # Normalize and validate tag name
    normalized_tag_name = _normalize_and_validate_tag_names([payload.tag_name])[0]
    
    # Find or create the tag
    tag = db.query(Tag).filter(Tag.name == normalized_tag_name).first()
    if not tag:
        tag = Tag(name=normalized_tag_name)
        db.add(tag)
        db.flush()  # Ensure tag gets an id before association
    
    # Associate if not already associated
    if tag not in note.tags:
        note.tags.append(tag)
    
    db.commit()
    db.refresh(note)
    
    # Build response with revision_id
    response_dict = note.to_dict()
    tag_ids = [tag.id for tag in note.tags]
    revision_id = compute_revision_id(note.title, note.body, tag_ids, note.updated_at.isoformat())
    response_dict["revision_id"] = revision_id
    
    return NoteResponse(**response_dict)


@router.delete("/notes/{note_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag(note_id: int, tag_id: int, db: Session = Depends(get_db)) -> None:
    """Remove a tag association from a note.
    
    Returns 204 (no content) on success.
    Returns 404 if note or tag does not exist, or if tag is not associated with note.
    
    Note: does NOT delete the tag itself (it may be associated with other notes).
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    
    if tag not in note.tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not associated with note")
    
    note.tags.remove(tag)
    db.commit()


@router.get("/search", response_model=SearchResponse)
def search_notes(
    q: str | None = Query(default=None, description="Text to search in title and body (case-insensitive substring match)"),
    tags: str | None = Query(default=None, description="Comma-separated tag names to filter by (AND logic)"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Results per page (1-100)"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    """Search notes by text (title and body) and optional tag filtering.
    
    Query parameter semantics:
    - q: case-insensitive substring match on title OR body (optional)
    - tags: comma-separated tag names (notes matching ALL tags are returned — AND logic)
    - page: 1-indexed page number (default 1)
    - page_size: results per page, capped at 100 (default 20)
    
    Returns paginated results with total_results count and has_more flag.
    
    Invariants enforced:
    - Text search is case-insensitive (ILIKE comparison)
    - Tag filtering uses AND logic: notes with ALL specified tags are returned
    - Pagination respects SQLite's LIMIT and OFFSET
    - Results ordered by updated_at DESC, then id DESC for determinism
    - total_results count includes all matching notes, not just current page
    - body_preview is truncated to 100 chars (optimized for rapid-rediscovery scanning per contract-note-search-response-envelope-rapid-rediscovery v1.1)
    
    Returns 200 with paginated SearchResponse.
    """
    # Build base query
    query_obj = db.query(Note)
    
    # Text search filter (case-insensitive substring match on title or body)
    if q:
        # SQLite LIKE is case-insensitive by default
        # Escape LIKE metacharacters (%, _) so they match literally
        escaped_q = _escape_like_pattern(q)
        search_pattern = f"%{escaped_q}%"
        query_obj = query_obj.filter(
            or_(
                _safe_ilike(Note.title, search_pattern),
                _safe_ilike(Note.body, search_pattern),
            )
        )
    
    # Tag filtering (notes matching ALL specified tags — AND logic)
    if tags:
        # Parse comma-separated tag names, strip whitespace
        tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        
        if tag_names:
            # Filter notes that have ALL of the specified tags (AND logic)
            # Chain .filter() calls: each adds an AND condition
            for tag_name in tag_names:
                query_obj = query_obj.filter(
                    Note.tags.any(Tag.name == tag_name)
                )
            # Use distinct() to avoid duplicate rows when joining on multiple tags
            query_obj = query_obj.distinct()
    
    # Count total matching notes (before pagination)
    total_count = query_obj.count()
    
    # Apply sorting and pagination
    # page is 1-indexed, so offset = (page - 1) * page_size
    offset = (page - 1) * page_size
    notes = (
        query_obj
        .order_by(Note.updated_at.desc(), Note.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )
    
    # Determine if there are more results
    has_more = (offset + page_size) < total_count
    
    # Build search results with body_preview (first 100 chars) instead of full body
    # Per contract-note-search-response-envelope-rapid-rediscovery (v1.1):
    # 100-char preview is optimized for Kohl's rapid-rediscovery scanning workflow
    search_results = []
    for note in notes:
        note_dict = note.to_dict()
        body_preview = note_dict["body"][:100]  # Truncate to 100 chars for scanning
        
        # Compute revision_id for consistency with GET /notes/{id}
        tag_ids = [tag.id for tag in note.tags]
        revision_id = compute_revision_id(note.title, note.body, tag_ids, note.updated_at.isoformat())
        
        search_result = SearchResultNote(
            id=note_dict["id"],
            title=note_dict["title"],
            body_preview=body_preview,
            tag_names=note_dict["tag_names"],
            tag_ids=note_dict["tag_ids"],
            created_at=note_dict["created_at"],
            updated_at=note_dict["updated_at"],
            revision_id=revision_id,
        )
        search_results.append(search_result)
    
    return SearchResponse(
        results=search_results,
        total_results=total_count,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )
