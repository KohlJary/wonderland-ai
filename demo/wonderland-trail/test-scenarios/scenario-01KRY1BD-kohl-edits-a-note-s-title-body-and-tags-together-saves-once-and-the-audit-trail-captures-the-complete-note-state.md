## Scenario 308: Kohl edits a note's title, body, and tags together, saves once, and the audit trail captures the complete note state

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601G
**Severity:** silent-wrongness

**Setup:**

Kohl opens a note. She edits: title (100 chars), body (2000 chars, markdown), and adds tags=['research', 'draft']. All edits are buffered to localStorage over 10 seconds of typing. She clicks Save.

**Trigger:**

POST /api/notes (or PUT /api/notes/{id}) sends {title, body, tag_names: ['research', 'draft']} to the server. Server processes atomically and logs to audit_trail table.

**Expected:**

Audit trail has one entry (one save event) with: note_id=42, timestamp=ISO8601 UTC, user_id=null (v1 single-user), saved_state_json={title, body, tag_names, tag_ids}, revision_id='v3', state_hash=<hash_of_saved_state>. The entry is complete and immutable (no updates, only appends). Later, a forensic query can reconstruct the note's exact state at the moment of save.

**Concern:**

If the audit trail is incomplete (missing body, or tags saved separately), forensic reconstruction is impossible. If the timestamp is naive or has no timezone, future audit queries may order events incorrectly. If the state_hash is wrong, tamper detection fails.

**Property:**

Audit trail completeness + forensic immutability
