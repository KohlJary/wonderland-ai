## Scenario 354: Kohl saves a note with title, body, and tags; the audit entry captures all three fields atomically

**GUID:** 01KRY1EAP8DPXCMJPQSNAEYA5S
**Severity:** breakage

**Setup:**

Kohl has opened the editor with a fresh note (no prior saves). Title is 'Research Notes', body is 'Initial findings on project X', tag_names are ['research', 'urgent']. localStorage has the draft buffered.

**Trigger:**

Kohl clicks the Save button.

**Expected:**

HTTP 200 response returns {id, title, body, tag_names, tag_ids, created_at, updated_at, revision_id}. An audit_log entry is created with: note_id (matches returned id), operator_id (system-assigned or Kohl's user ID), saved_state (JSON of {title, body, tag_ids}), revision_id (opaque hash), timestamp (server-assigned), collision_detected=false. The entry is readable via audit queries and no fields are truncated.

**Concern:**

If saved_state is truncated (e.g., body over 16KB gets silently cut), forensic reconstruction will be incorrect and Kohl's work is unrecoverable. If audit_log entry is missing any field, reconstruction fails. If the entry is not created atomically with the note save, a server crash mid-transaction leaves the note without a log entry, breaking the audit trail's core promise.

**Property:**

audit_log entry captures complete note state (title, body, tag_ids) at save time; entry is created in same transaction as note write; no truncation or field omission occurs

**Implies:**
- Audit entry must be created before save response is returned to client
- saved_state JSON serialization must handle empty strings and empty arrays correctly
- revision_id must be deterministic (same state always produces same hash)
