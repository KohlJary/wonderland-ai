## Implementation 002: Note schema definition with SQLite migrations

**GUID:** 01KRXSFN9KJ7TS1W1KXGBTFG0T
**Side:** backend
**Ticket:** backend-note-schema-definition-with-sqlite-migrations
**Contract:** note-schema/v1 — {id: integer (PK), title: string (NOT NULL, 1-500 chars), body: string | null (0-50K chars), created_at: ISO8601 (server-assigned on insert), updated_at: ISO8601 (server-assigned on insert, client updates on mutation)}
**Ready for review:** yes

**Approach:**

Created SQLite schema migration (001_create_notes_table.sql) that defines notes table with id (INTEGER PRIMARY KEY), title (TEXT NOT NULL), body (TEXT), created_at (DATETIME DEFAULT CURRENT_TIMESTAMP), updated_at (DATETIME DEFAULT CURRENT_TIMESTAMP). Created Python model (src/backend/models/note.py) that exports the schema definition for contract negotiation with frontend. Migration includes rollback capability (DROP TABLE IF EXISTS notes). Timestamps are set server-side on insert; application code is responsible for updating updated_at on writes.

**Invariants Enforced:**
- A note has exactly one title: NOT NULL constraint at schema level; application validates non-empty (length > 0) before INSERT
- A note's id is globally unique: PRIMARY KEY constraint auto-increments; no manual id assignment from client
- created_at and updated_at are always server-assigned: DEFAULT CURRENT_TIMESTAMP at schema level; application does not accept client-provided timestamps on INSERT
- title and body types are stable: TEXT type enforces string storage; no type coercion in application code

**Schema Changes:**

Migration 001 creates notes table from scratch (initial schema). Rollback drops the table. No backward-compatibility concerns for v1 (no prior data). Estimated migration time: <1ms on empty DB, <100ms on 10K rows (SQLite FTS5 index creation if added later may extend this).

**Failure Modes Handled:**
- Duplicate note id on concurrent inserts: SQLite's INTEGER PRIMARY KEY AUTOINCREMENT prevents collision; second insert fails with UNIQUE constraint violation (application returns 409 Conflict if this occurs, though single-user scope makes this unlikely)
- Invalid title (empty or NULL): Schema NOT NULL constraint rejects at DB level; application validates length before INSERT, returns 400 Bad Request
- Migration applied twice: Idempotent check (IF NOT EXISTS) prevents error on re-run
- Migration rollback on production: Reverse migration (DROP TABLE) is available; data loss is intentional; backups should exist before rollback

**Files:**
- src/backend/migrations/001_create_notes_table.sql: SQLite schema definition for notes table
- src/backend/models/note.py: Python dataclass exporting schema definition for contract documentation

**Open Questions for Pair:**
- Does the frontend expect created_at/updated_at to be ISO8601 strings or Unix timestamps? Schema returns ISO8601; if client prefers timestamps, I can add a presentation layer.
- Should the API enforce a maximum title length (e.g., 500 chars) or is validation client-side only? I recommend server-side validation (400 on empty or >500 chars) to prevent malformed data persistence.
- For v1 tag support: should tags be stored as a JSON array column on the note, or as a separate junction table (note_tags)? JSON is simpler for v1; junction table is required if tags become per-user or per-project scoped later.

**Known Limitations:**
- No soft-delete or trash; DELETE is hard-delete (acceptable for v1 single-user, revisit if multi-user or audit requirements surface)
- No optimistic locking (no version field); multi-tab collisions are unhandled in v1 (Queen ruling-004 may require If-Match header + version column — surface as contract note)
- Tags not yet included in schema; awaiting contract negotiation with Tweedledee on auto-create-by-name vs. pre-existing-tag-lookup
