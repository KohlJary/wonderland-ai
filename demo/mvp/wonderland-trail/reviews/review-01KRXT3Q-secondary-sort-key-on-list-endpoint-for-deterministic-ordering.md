## Review 011: Secondary sort key on list endpoint for deterministic ordering

**GUID:** 01KRXT3QP1KXYAN3TVS8RW3PNS
**Files reviewed:** src/backend/api/notes.py
**Verdict:** accept

### Findings

#### suggestion: Add secondary sort by id to prevent flaky tests
**Location:** src/backend/api/notes.py, line 134
**Quote:**

```
notes = db.query(Note).order_by(Note.updated_at.desc()).all()
```

**Read:** Endpoint orders by updated_at DESC (newest first), which is correct. However, if two notes have the same updated_at timestamp (common in rapid tests), the tie-breaker is undefined. SQLite returns them in insertion order, but that's an implementation detail, not guaranteed.
**Concern:** Nondeterministic ordering makes tests flaky. A test verifying 'first note has highest id' might pass or fail randomly. This is degradation — tests are unreliable.
**Request:** Add secondary sort: `.order_by(Note.updated_at.desc(), Note.id.desc())`. If two notes have same updated_at, higher id appears first. This is deterministic and stabilizes tests.

### Approvals

- All seven CRUD endpoints implemented per contract-note-003
- Response shape matches contracts exactly
- Tag auto-creation is atomic
- Validation is precise and correct
- Timestamp handling prevents silent timezone bugs
- Many-to-many relationship is cleanly designed
