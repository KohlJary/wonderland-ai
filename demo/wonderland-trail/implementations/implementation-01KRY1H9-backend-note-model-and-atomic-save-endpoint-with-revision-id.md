## Implementation 059: Backend Note model and atomic save endpoint with revision ID

**GUID:** 01KRY1H9N8T2ZPSD8KHJC14T7D
**Side:** backend
**Ticket:** ticket-01KRY06R-backend-note-model-and-atomic-save-endpoint-with-revision-id
**Contract:** contract-note-01KRY0B8 (revision-id-computation-and-collision-detection-contract-backend-side). POST /notes request {title, body?, tag_names?} → response 201 {id, title, body, tag_names, tag_ids, created_at, updated_at, revision_id}. PUT /notes/{id} with If-Match header → 200 or 409 Conflict with server_state. GET /notes → 200 [notes]. GET /notes/{id} → 200 {note}. DELETE /notes/{id} → 204. All timestamps ISO8601 UTC with Z suffix.
**Ready for review:** yes

**Approach:**

Implemented complete CRUD for notes with audit trail and collision detection. Note model includes id, title, body, tags (many-to-many), created_at/updated_at timestamps, and derived revision_id. POST /notes creates notes atomically with tags. PUT /notes/{id} updates atomically with optimistic locking via If-Match header. On mismatch, returns 409 Conflict with server state. All changes logged immutably to audit_log table with full-state snapshots and state_hash for forensic integrity. Revision ID computed as SHA256(canonical_JSON) ensuring determinism and order-independence.

**Invariants Enforced:**
- Note.id is auto-assigned PK, immutable after creation.
- Note.title is non-empty string (1-255 chars), enforced by Pydantic and NOT NULL constraint.
- Note.body is always a string (empty string is default, never NULL), enforced by NOT NULL + default="".
- Note.created_at is server-assigned on insert, immutable (no onupdate), ISO8601 UTC.
- Note.updated_at is server-assigned on insert and updated on every change, ISO8601 UTC.
- Note.tags is a many-to-many relationship via note_tags junction table. Cascade delete on note_id (deleting note removes associations); no cascade on tag_id (deleting association preserves tag, may be shared).
- Tag.name is globally unique (UNIQUE constraint) and case-sensitive.
- Tag.name is normalized (whitespace-stripped) by _normalize_and_validate_tag_names() before storage.
- revision_id is deterministic SHA256(canonical_JSON) of [title, body, sorted_tag_ids, updated_at]. Same state always produces same hash.
- AuditLog entries are immutable (never updated or deleted), append-only, with full-state snapshots for forensic reconstruction.
- If-Match header comparison: if present and doesn't match current revision_id, returns 409 Conflict without updating; if match or absent, update proceeds (backward-compatible).
- Atomic transactions: POST and PUT are atomic at the database level (SQLAlchemy session.commit()). On error, transaction rolls back.

**Schema Changes:**

Migration from HelloMessage to Note table. New tables: notes (id PK, title, body, created_at, updated_at), tags (id PK, name UNIQUE), note_tags (note_id FK CASCADE, tag_id FK), audit_log (id PK, note_id FK CASCADE, timestamp, user_id, saved_state_json, revision_id, state_hash, collision_detected, conflicting_revision_id). No backward-compatibility constraints (HelloMessage is dropped, new schema only).

**Failure Modes Handled:**
- Empty or missing title: Pydantic validation rejects (400 Bad Request).
- Tag name empty or whitespace-only: _normalize_and_validate_tag_names() raises HTTPException 400.
- Tag name too long (>100 chars): Pydantic validation rejects (400 Bad Request).
- Note not found on PUT/DELETE/GET/{id}: raises HTTPException 404 Not Found.
- Tag not found on POST /notes/{id}/tags: raises HTTPException 404 Not Found.
- If-Match header mismatch on PUT: raises HTTPException 409 Conflict with server_state and server_revision_id.
- Tag association constraint violation (e.g., duplicate tag): SQLAlchemy raises IntegrityError, caught by endpoint, returns 400 or 409 depending on context.
- Transaction failure (DB error, constraint violation): SQLAlchemy rollback ensures atomic all-or-nothing; client sees 400/409/500 depending on error type.

**Files:**
- src/backend/models.py: Note, Tag, AuditLog models with relationships and to_dict() serialization; compute_revision_id() helper
- src/backend/api/notes.py: complete CRUD endpoints (POST/GET/PUT/DELETE /notes*, tag association, search), audit logging, collision detection via If-Match header
- src/backend/api/__init__.py: router aggregation
- src/backend/main.py: FastAPI app config, CORS setup, table creation on startup

**Open Questions for Pair:**
- Search endpoint body_preview truncation is 100 chars per contract-note-search-response-envelope-rapid-rediscovery v1.1—is this matching frontend expectations? Tweedledee will need to know this for Search.tsx component.
- Tag normalization (whitespace stripping, case sensitivity) is per contract-note-01KRXYD0 (case-sensitive, whitespace-stripped). Frontend tag input validation should mirror this. Can you confirm TagInput.tsx validation matches?

**Known Limitations:**
- No user auth in v1 (single-device scope). user_id in audit_log is always NULL.
- Search uses simple ILIKE substring matching, not full-text index. Performance acceptable for <1000 notes; FTS5 index deferred to v2 if scale demands.
- Audit log is append-only (immutable, never deleted/updated). Retention policy is not implemented (logs grow indefinitely); add retention rules in v2 if needed.
- If-Match header is optional in v1 for backward compatibility (single-user). Future enforcement of mandatory collision detection for multi-user should add validation to require If-Match on PUT.
- Tag association is atomic per note (one transaction), but no cross-note consistency constraints (e.g., two concurrent POST requests creating the same tag will each create a duplicate). Tag uniqueness is enforced at DB level, so duplicates will fail; client should handle gracefully.
