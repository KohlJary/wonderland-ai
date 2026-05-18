## Implementation 001: POST /api/notes and GET /api/notes/{id} endpoints

**GUID:** 01KRXSDSCX79ZCA58FRPVZJ3ZS
**Side:** backend
**Ticket:** backend-note-create-and-read-endpoints
**Contract:** contract-note-001-008: POST /api/notes {title: str, body?: str, tag_ids?: str[]} → 201 {id, title, body, tags, created_at, updated_at}. GET /api/notes/{id} → 200 {id, title, body, tags, created_at, updated_at} or 404 not found. All timestamps ISO8601.
**Ready for review:** yes

**Approach:**

NoteCreate pydantic model validates title (non-empty), body (optional, defaults to empty string), tag_ids (optional, defaults to empty list). POST /api/notes creates Note row, commits, refreshes, and returns NoteResponse with ISO8601 timestamps. GET /api/notes/{id} queries by id, returns 404 if not found, otherwise NoteResponse. Note.to_dict() serializes timestamps via isoformat() to ISO8601 format.

**Invariants Enforced:**
- title is required and non-empty (1–255 chars): enforced by pydantic Field(min_length=1, max_length=255) on NoteCreate
- body is optional and defaults to empty string: Field(default='') ensures no null in JSON response
- tags is optional and defaults to empty list: Field(default_factory=list) ensures no null, always an array
- id is auto-assigned: SQLAlchemy autoincrement primary key
- created_at is immutable: set once on insert via SQLAlchemy server_default=func.now(), never updated
- updated_at is always current: set on insert and updated on every row modification via onupdate=func.now()
- all timestamps are ISO8601: enforced by to_dict() calling isoformat() on datetime objects

**Schema Changes:**

SQLite schema migration from hello_messages table to notes table. New columns: title (VARCHAR 255 NOT NULL), body (TEXT nullable, default=''), tags (JSON nullable, default='[]'), updated_at (DATETIME with timezone, server-default now(), onupdate now()). Indexes: default SQLite PK on id. Migration is one-time schema swap (dev mode via create_all on app startup). For production, would use Alembic with explicit migration scripts.

**Failure Modes Handled:**
- POST /api/notes with missing/empty title: pydantic validation error, returns 422 with validation details
- POST /api/notes with missing/empty body: body defaults to empty string, no error
- GET /api/notes/{id} with nonexistent id: query returns None, endpoint raises HTTPException(404, 'Note not found')
- POST /api/notes database write failure: SQLAlchemy exception propagates, FastAPI converts to 500
- Concurrent POST /api/notes creating same title: no uniqueness constraint, both succeed with different ids (acceptable for v1)

**Files:**
- src/backend/api/notes.py: new file, POST /api/notes and GET /api/notes/{id} endpoints with pydantic models
- src/backend/models.py: Note model replacing HelloMessage placeholder (title, body, tags JSON, created_at, updated_at)
- src/backend/api/__init__.py: import notes_router, include in api_router with /api prefix
- tests/test_notes.py: new test file covering create minimal/with-body/with-tags, retrieve, not-found, validation, timestamps
- tests/conftest.py: unchanged, fixture already supports in-memory SQLite

**Open Questions for Pair:**
- On frontend error handling for POST /api/notes failures (4xx vs 5xx): does the NoteResponse shape (including error responses) match what you're expecting? If validation fails (empty title, etc.), we return pydantic 422; if server error, we return 500. Should I add explicit error response models for clarity?

**Known Limitations:**
- Tag system is denormalized JSON array (v1 assumption per contract-note-005). Tag filtering/autocomplete deferred to v2.
- No conflict resolution on concurrent edits — last write wins (expected for single-user v1 per contract-note-006).
- No idempotency keys — if POST /api/notes succeeds server-side but response is lost, client will create duplicate on retry (acceptable for v1 single-device assumption).
- No soft-delete; DELETE endpoint not yet implemented (contract-note-001 specifies hard-delete for v1).
