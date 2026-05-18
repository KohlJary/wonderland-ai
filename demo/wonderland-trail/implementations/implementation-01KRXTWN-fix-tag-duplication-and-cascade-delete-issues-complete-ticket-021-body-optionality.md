## Implementation 014: Fix tag duplication and cascade delete issues, complete Ticket 021 body optionality

**GUID:** 01KRXTWNFXJ0WG66Y93ZM0QNJM
**Side:** backend
**Ticket:** ticket-01KRXTQXFPAKBVMQRQXZ8WWM20
**Contract:** message-envelope/v3 (NoteCreate.body: str | None = default=None, stored as empty string in database)
**Ready for review:** yes

**Approach:**

Three fixes: (1) Added db.flush() in _associate_tags after creating new tags to prevent UNIQUE constraint violation when request has duplicate tag names; (2) Removed cascade="all, delete" from Note.tags relationship to prevent cascade-deleting shared tags when a note is deleted; (3) Added secondary sort by Note.id.desc() to list endpoint for deterministic ordering. Ticket 021 body type signature was already correct in the current codebase.

**Invariants Enforced:**
- Tag names are globally unique (UNIQUE constraint on tags.name)
- Each note has exactly one title (required, 1-255 chars)
- Each note's body is always a string, never NULL (stored as empty string if not provided)
- Tags persist when notes are deleted (shared tag associations are only deleted, not the tag itself)
- List endpoint returns notes in reverse chronological order by updated_at, with deterministic tiebreaking by id

**Schema Changes:**

None (no new columns or tables; fixes are behavioral)

**Failure Modes Handled:**
- Duplicate tag names in request: deduped in-memory before database write, preventing UNIQUE constraint violations
- Concurrent tag creation: flush() after creating new tag ensures it's persisted before attempting association
- Shared tags on deletion: no cascade delete on relationship; database foreign key constraint deletes association only
- Non-deterministic list ordering: secondary sort by id DESC ensures stable ordering for tests and UI

**Files:**
- src/backend/api/notes.py: Added db.flush() in _associate_tags (line 127), added secondary sort in list_notes (line 143)
- src/backend/models.py: Removed cascade="all, delete" from Note.tags relationship (line 45), removed cascade from Tag.notes relationship (line 98)
