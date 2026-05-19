## Scenario 355: Kohl saves the same note twice with identical content; both audit entries are created with identical revision_id

**GUID:** 01KRY1EAP8DPXCMJPQSNAEYA5T
**Severity:** silent-wrongness

**Setup:**

Kohl has saved a note once (audit entry 001 exists with revision_id='abc123def456'). She then makes no edits and clicks Save again (same title, body, tags).

**Trigger:**

Second Save button click.

**Expected:**

HTTP 200 returns the same note with revision_id='abc123def456' (deterministic). A second audit_log entry is created with: the same saved_state JSON, the same revision_id='abc123def456', a different timestamp (server time has advanced). Both entries exist in the audit log, distinguishable by id and timestamp, but identical in content_hash (if that's computed).

**Concern:**

If the revision_id changes on a no-op save (non-deterministic hash), collision detection will break: a second tab saving the same state will think there's a conflict even though nothing changed. If the second audit entry is not created (deduplication error), the audit trail is incomplete and can't answer 'how many times was this note saved?'

**Property:**

revision_id is deterministic: hash(same_state) always produces same revision_id; audit_log entries are created for every save, including no-op saves; no deduplication skips audit logging
