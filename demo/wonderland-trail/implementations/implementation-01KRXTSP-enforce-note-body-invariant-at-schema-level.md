## Implementation 011: Enforce Note.body invariant at schema level

**GUID:** 01KRXTSPYEYM76F1H6Q8J8BXNQ
**Side:** backend
**Ticket:** note-body-nullable-true-contradicts-to-dict-guard-and-contract
**Contract:** Note.body is always a string (empty string is default, never NULL). Matches contract requirement that body in responses is always string type.
**Ready for review:** yes

**Approach:**

Changed Column definition from `nullable=True, default=""` to `nullable=False, default=""`. This moves the invariant enforcement from application code (the to_dict() guard) to the database schema, where it cannot be bypassed. Removed the redundant `or ""` guard in to_dict().

**Invariants Enforced:**
- Note.body is always a string: enforced by `nullable=False, default=""` at the database schema level

**Schema Changes:**

SQLite column constraint: notes.body TEXT NOT NULL DEFAULT ''. Any existing notes with NULL body would violate this constraint on the next schema update. Since this is a development schema (using create_all), existing dev data will be cleared; production deployments would require an Alembic migration with UPDATE to backfill empty strings.

**Failure Modes Handled:**
- Reading note.body outside to_dict() and encountering None: prevented by schema-level NOT NULL constraint

**Files:**
- src/backend/models.py: Changed Line 42 Column definition; updated Line 28 docstring; removed Line 79 guard in to_dict()
