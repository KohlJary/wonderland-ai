## Scenario 303: Kohl saves a note with title and body, backend persists it and returns revision_id

**GUID:** 01KRY1BD9QYCM0QJV0RZ20601B
**Severity:** breakage

**Setup:**

Kohl opens the editor with a blank note (noteId is null). She types title='Mitochondrial function notes' and body='The mitochondria is the powerhouse...' (200 chars, markdown). She clicks Save.

**Trigger:**

POST /api/notes with {title, body, tag_names: []} from the editor

**Expected:**

Server responds 201 with {id: <new_int>, title, body, tag_names: [], tag_ids: [], created_at: ISO8601 UTC Z, updated_at: ISO8601 UTC Z, revision_id: <opaque_hash>}. Note is persisted to SQLite. Kohl's editor receives the id and revision_id, clears localStorage, shows 'Saved' feedback for 1-2s.

**Concern:**

If the backend fails to persist atomically (partial write), or returns a malformed response, or computes revision_id incorrectly, Kohl's first save fails silently or corrupts the audit trail. This is the foundational save contract.

**Property:**

Save endpoint atomic write + revision_id determinism
