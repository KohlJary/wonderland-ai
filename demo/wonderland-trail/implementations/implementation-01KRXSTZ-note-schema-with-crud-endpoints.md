## Implementation 004: Note schema with CRUD endpoints

**GUID:** 01KRXSTZ9T61V2B6EDVX7HRVQR
**Side:** backend
**Ticket:** test-failed-tests-test-notes-py-test-timestamps-iso8601
**Contract:** contract-note-001/v1 (Note model and CRUD endpoint contract), contract-note-004/v1 (Note Creation Envelope with Tags), contract-note-008/v1 (Search endpoint contract). Request: POST /notes {title: str, body?: str, tag_ids?: str[]}. Response: {id, title, body, tags: [str], created_at: ISO8601Z, updated_at: ISO8601Z}.
**Ready for review:** yes

**Approach:**

SQLAlchemy Note and Tag models with server-side timestamp generation and immutable created_at. Seven REST endpoints: POST /notes (create), GET /notes (list reverse-chronological), GET /notes/{id} (read), PUT /notes/{id} (update), DELETE /notes/{id} (delete), POST /notes/{id}/tags (associate tag), DELETE /notes/{id}/tags/{tag_id} (remove tag). Tags auto-created on first use. All timestamps returned as ISO8601 UTC with 'Z' suffix.

**Invariants Enforced:**
- Note.title is non-empty string (validated on POST/PUT, 1-255 chars, NOT NULL in schema)
- Note.body is optional text field (defaults to empty string, permits empty/null on reads)
- Note.id is auto-incrementing primary key (unique, immutable)
- created_at is set server-side on insert, never modified (immutable, initialized via server_default=func.now())
- updated_at is set server-side on insert and updated on every write (via server_default and onupdate=func.now())
- All timestamps are timezone-aware UTC and serialized as ISO8601 with Z suffix (ensure_tz_aware() enforces this)
- Tags are auto-created on first reference via tag_ids in POST/PUT (idempotent, case-sensitive unique by name)
- Tag associations are atomic per note (tag_ids provided replaces all existing tags in single transaction)

**Schema Changes:**

CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT DEFAULT '', created_at DATETIME(timezone=True) NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME(timezone=True) NOT NULL DEFAULT CURRENT_TIMESTAMP). CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE). CREATE TABLE note_tags (note_id INTEGER PRIMARY KEY, tag_id INTEGER PRIMARY KEY, FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE, FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE). Backward-compatible: fresh schema, no migrations. Reversible: DROP TABLE note_tags, DROP TABLE tags, DROP TABLE notes restores empty state.

**Failure Modes Handled:**
- Missing title on POST: 422 validation error (Pydantic enforces min_length=1)
- Empty title on POST: 422 validation error
- Non-existent note_id on GET/PUT/DELETE: 404 not found
- Tag creation failure (e.g., max length exceeded): 422 validation error on tag_ids input
- Concurrent note inserts: SQLite autoincrement handles this atomically per row-lock; both inserts succeed with unique IDs
- Server datetime unavailable: ensure_tz_aware() falls back to datetime.now(timezone.utc) on None

**Files:**
- src/backend/models.py: Note and Tag models with server-side timestamps, to_dict() serialization with ensure_tz_aware() producing ISO8601 Z format
- src/backend/api/notes.py: Seven endpoints (POST create, GET list, GET by id, PUT update, DELETE, POST tag-associate, DELETE tag-remove) with validation and error handling
- src/backend/api/__init__.py: Router aggregation (unchanged, already includes notes router)
- src/backend/main.py: App wiring with CORS and lifespan handler (already correct)

**Open Questions for Pair:**
- Tags are returned in response as simple list of strings per contract-note-004. Is this the right shape for your editor state, or do you need tag objects with {id, name}?

**Known Limitations:**
- No pagination on GET /notes endpoint yet (returns all notes unsorted); pagination deferred to search-endpoint work per contract-note-008
- No audit logging yet (Queen ruling-003 deferred); endpoints don't write to audit_log table
- No multi-tab collision detection (Queen ruling-004 If-Match header deferred); PUT /notes/{id} has no version check
