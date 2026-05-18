## Scenario 353: Note update and tag association happen atomically; if tag association fails, entire transaction rolls back

**GUID:** 01KRY1DY1PSMHZM094C8W7E46T
**Severity:** silent-wrongness

**Setup:**

Note update and tag changes are part of the same transaction. A constraint violation occurs during tag association.

**Trigger:**

Backend begins transaction, updates note, then fails to associate tags (e.g., duplicate tag name constraint).

**Expected:**

Entire transaction rolls back. Note remains unchanged. Frontend receives error and can retry.

**Concern:**

If note is committed before tags, they become inconsistent. Revision_id computed from partial state causes spurious collision detection.

**Property:**

For all PUT /notes/{id} with tag changes, transaction is all-or-nothing.

**Implies:**
- Implies entire _associate_tags() wrapped in same db.commit() as note update.
