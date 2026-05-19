## Scenario: Note update and tag association happen atomically; if tags fail to save, entire transaction rolls back

**Severity:** silent-wrongness

**Setup:**
Note id=1 with tags=['old_tag']. Client sends PUT with title='new', body='new', tag_names=['new_tag']. Both the note update and tag association are part of the same transaction.

**Trigger:**
Backend begins transaction, updates note (title, body), dissociates old tags, associates new tags. Before commit, a constraint violation occurs (e.g., new_tag has a uniqueness constraint that was violated concurrently).

**Expected:**
Entire transaction rolls back. The note remains unchanged: title='original', body='original', tags=['old_tag']. The frontend receives 500 or 409 (depending on the error type) and can retry or escalate.

**Concern:**
If the transaction is loose (e.g., note is committed but tag updates fail), the note and tags become inconsistent. The revision_id will be computed from the partially-updated state, and future edits will fail with spurious collision detection or state corruption.

**Property:**
For all PUT /notes/{id} requests that involve both note field updates and tag updates, the transaction is all-or-nothing. Either all changes commit or none do.

**Implies:**
- Implies the entire _associate_tags() call must be wrapped inside the same db.begin() / db.commit() transaction as the note update.
- Implies that db.flush() is used for intermediate steps (e.g., flushing the note to get its ID), but db.commit() happens only at the end.
- Implies test should simulate a tag uniqueness constraint violation mid-transaction and verify rollback.

