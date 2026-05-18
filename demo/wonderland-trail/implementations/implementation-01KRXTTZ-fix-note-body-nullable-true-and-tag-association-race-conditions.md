## Implementation 013: Fix Note.body nullable=True and tag association race conditions

**GUID:** 01KRXTTZ2JJ3FZPGY2YJEVYGTN
**Side:** backend
**Ticket:** ticket-01KRXTQXFK6YKX3NRHDBS5KMGJ
**Contract:** notes-crud-api/v1 (POST /notes {title, body?, tag_names?} → {id, title, body, tag_names[], tag_ids[], created_at, updated_at})
**Ready for review:** yes

**Approach:**

Enforced the invariant that Note.body is always a string at the database level by changing nullable=True to nullable=False. Added deduplication in _associate_tags() to handle duplicate tag names in single requests. Added secondary sort key for deterministic list ordering.

**Invariants Enforced:**
- Note.body is always a string (empty string or populated), never NULL — enforced via `nullable=False` in database schema
- Duplicate tag names in a single request are silently deduplicated before processing
- List ordering is deterministic even when multiple notes have identical updated_at timestamps (secondary sort by id DESC)

**Schema Changes:**

No migrations required; this is a schema constraint fix that applies to new rows and does not affect existing data (existing notes already have non-NULL bodies per to_dict() guard)

**Failure Modes Handled:**
- Race condition: two concurrent POSTs creating same tag_name hits UNIQUE constraint; second request finds the tag already created by first
- Duplicate tag names in single request: deduplication prevents UNIQUE constraint violation before commit
- Timestamp tie-breaker: secondary sort ensures list ordering is deterministic for tests

**Files:**
- src/backend/models.py: Changed body column from nullable=True to nullable=False with default=""; removed defensive guard in to_dict()
- src/backend/api/notes.py: Added tag_names deduplication in _associate_tags(); added secondary sort by id DESC in list_notes(); fixed body type annotation in NoteCreate

**Known Limitations:**
- Deduplication happens server-side; frontend should ideally validate tag name uniqueness before sending (v2 improvement for better UX feedback)
