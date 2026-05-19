## Implementation 008: Note and Tag CRUD endpoints with schema

**GUID:** 01KRXTEM429E094SPPV0VPVKRD
**Side:** backend
**Ticket:** backend-note-and-tag-crud-endpoints-with-schema
**Contract:** contract-note-01KRXRVT/v1 (Note Creation Envelope with Tags). Request POST /notes: {title: string, body?: string, tag_names?: string[]}. Response: {id, title, body, tag_names: [string], tag_ids: [int], created_at (ISO8601 UTC), updated_at (ISO8601 UTC)}. GET /notes returns reverse chronological (updated_at DESC).
**Ready for review:** yes

**Approach:**

SQLite schema: Note (id, title, body, created_at, updated_at), Tag (id, name, globally unique), note_tags (many-to-many junction). Endpoints: POST /notes (create with auto-tag), GET /notes (list, reverse chrono), GET /notes/{id} (read), PUT /notes/{id} (update title/body/tags), DELETE /notes/{id} (cascade). Tag seam: POST /notes/{id}/tags (auto-create), DELETE /notes/{id}/tags/{tag_id} (remove assoc). All responses include tag_names and tag_ids. Validation: title non-empty, body optional, tag names unique globally.

**Invariants Enforced:**
- Note.title is non-empty (String NOT NULL in schema, Field min_length=1 in Pydantic)
- Note.id is stable and unique (INTEGER PRIMARY KEY AUTOINCREMENT)
- Tag.name is globally unique (UNIQUE constraint in schema)
- Note-Tag association is many-to-many (note_tags junction table with FKs, cascade delete)
- Each note has exactly one created_at (set on insert, immutable server-side)
- Each note has exactly one updated_at (set on insert, updated on each change, via func.now() server-side)
- Tags are never null in response (empty list [] if no tags, never null)
- Timestamps are always UTC ISO8601 with explicit Z suffix (to_dict() ensures timezone-aware)

**Schema Changes:**

New tables: notes (id INTEGER PK, title STRING NOT NULL, body TEXT, created_at DATETIME, updated_at DATETIME), tags (id INTEGER PK, name STRING UNIQUE NOT NULL), note_tags (note_id FK, tag_id FK, both PK, ON DELETE CASCADE). Migration: straightforward from hello_messages placeholder. Backward compatibility: N/A (v1 baseline).

**Failure Modes Handled:**
- Empty title: POST/PUT returns 422 Validation Error (Pydantic min_length=1)
- Title too long: 422 Validation Error (max_length=255)
- Tag name too long: 422 Validation Error (max_length=100)
- Missing note: GET/PUT/DELETE/{id} returns 404 (explicitly checked before operation)
- Missing tag for association: POST /notes/{id}/tags auto-creates if missing; DELETE returns 404 if not found
- Tag not associated: DELETE /notes/{id}/tags/{tag_id} returns 404 if tag not on note
- Duplicate tags in create: tag_names list can contain duplicates; only unique tags are associated (set logic in _associate_tags)
- Network/DB failure: no explicit retry; FastAPI auto-converts SQLAlchemy exceptions to 500

**Files:**
- src/backend/models.py: Note class (title, body, tags relationship), Tag class (name unique), note_tags junction table, to_dict() serialization
- src/backend/api/notes.py: NoteCreate/NoteUpdate/NoteResponse/TagCreate Pydantic models, POST/GET/PUT/DELETE note endpoints, tag association endpoints with auto-create logic
- src/backend/db.py: SQLAlchemy session factory, engine config
- src/backend/main.py: FastAPI app setup, Base.metadata.create_all()

**Open Questions for Pair:**
- Frontend expecting tag_names and tag_ids in response? Code provides both per contract-note-01KRXRVT — confirm consumption in api.ts

**Known Limitations:**
- No pagination on GET /notes; deferred to search-endpoint work (contract-note-01KRXSMH)
- No audit logging; Queen ruling-003 deferred to v2
- No If-Match versioning; Queen ruling-004 deferred to v2
- Single-device assumption (no auth layer per requirements)
