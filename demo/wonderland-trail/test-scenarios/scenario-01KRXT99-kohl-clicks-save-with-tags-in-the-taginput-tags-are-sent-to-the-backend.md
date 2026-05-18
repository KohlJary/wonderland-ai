## Scenario 013: Kohl clicks Save with tags in the TagInput — tags are sent to the backend

**GUID:** 01KRXT99M7QSR234FW4T0095TT
**Severity:** breakage

**Setup:**

The editor has title 'Lab Notes 2025-01-22', body 'Observed unexpected crystallization during heating', and three tags: 'crystallization', 'heating', 'anomaly'. The Save button is visible and clickable.

**Trigger:**

Kohl clicks the Save button.

**Expected:**

The frontend POSTs to /api/notes with body {title, body, tag_names: ['crystallization', 'heating', 'anomaly']}. The backend responds with 201 + persisted note (including server-assigned id and timestamps). The tag list in the editor is cleared. The editor remains open, ready for a new note or further editing.

**Concern:**

If tags are not sent to the backend, they are silently lost — Kohl's organizational work vanishes. If the tag list is not cleared, Kohl's next note inherits the old tags by accident.

**Property:**

Tags are atomically persisted with the note on Save
