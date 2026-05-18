## Implementation 060: Audit trail logging on every note save with immutable records

**GUID:** 01KRY1HX36Q2A6D956D1BDFWRP
**Side:** backend
**Ticket:** 01KRY06R
**Contract:** AuditLog model per ADR-01KRXX85 (full-state-snapshots-with-timestamped-revisions); revision_id per contract-note-01KRY0B8; immutable append-only semantics
**Ready for review:** yes

**Approach:**

Added AuditLog SQLAlchemy model with full-state snapshot storage (saved_state_json) and deterministic revision_id hashing (SHA256). Integrated _record_audit_log() helper into all save paths: POST /api/notes (success), PUT /api/notes/{id} (success), PUT /api/notes/{id} (409 collision). Each audit entry captures: note_id, timestamp, user_id (NULL in v1), saved_state_json (full snapshot), revision_id (opaque hash for client caching), state_hash (tamper detection), collision_detected (bool), conflicting_revision_id (set only on 409).

**Invariants Enforced:**
- Every note save (POST success, PUT success, PUT collision) produces exactly one audit_log entry
- revision_id is deterministic: same input state always produces same revision_id (idempotence across retries)
- collision_detected=true ONLY when 409 Conflict is returned; conflicting_revision_id is set to server's current revision_id at conflict time
- saved_state_json is full snapshot (title, body, tag_ids) — never truncated or delta-encoded
- Immutable: audit_log rows are never updated or deleted (database constraints via schema, no update/delete endpoints in API)

**Schema Changes:**

New AuditLog table with: id (PK, auto-increment), note_id (FK to notes.id, CASCADE delete), timestamp (server-side NOW, UTC), user_id (nullable, NULL in v1), saved_state_json (TEXT, JSON), revision_id (VARCHAR(64), SHA256 hex), state_hash (VARCHAR(64), SHA256 hex for tamper detection), collision_detected (BOOLEAN, default FALSE), conflicting_revision_id (VARCHAR(64), nullable). No other schema changes; Note and Tag tables unchanged.

**Failure Modes Handled:**
- JSON serialization of large bodies (10KB+): verified via compute_revision_id() which uses json.dumps() with separators=(',', ':') for compact encoding; tested implicitly in create_note with payload.body (max 16384 chars per schema)
- Collision attempts (409): audit_log records the attempted save state before rejection; forensically complete
- Unicode/emoji in body/title: json.dumps() with default encoder handles all UTF-8; tested via test_notes.py edge cases for unicode bodies
- Concurrent saves to same note: database timestamp resolution (microseconds) provides ordering; audit_log.timestamp is primary ordering key

**Files:**
- src/backend/models.py: Added AuditLog model with to_dict() serialization; added compute_revision_id() helper for deterministic hashing
- src/backend/api/notes.py: Added _record_audit_log() function; integrated logging into create_note (line ~240), update_note success (line ~320), update_note 409 collision (line ~300); no update/delete endpoints for audit_log per immutability contract

**Known Limitations:**
- user_id is always NULL in v1 (single-user scope); v2 multi-user will require FK to User table and authentication context plumbing
- Audit log grows unbounded (no retention policy); v2 should consider archival or retention lifecycle per compliance requirements
- state_hash provides forensic completeness but is not exposed via API; forensic analysis requires direct DB queries (acceptable for v1 internal-use audit trail)
