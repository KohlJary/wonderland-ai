## Scenario 067: Kohl creates a note with a very long body (15,000 characters of markdown), saves it, and retrieves it; the full body is persisted and renderable

**GUID:** 01KRXTE35W88GEZR30A8W5VQ4F
**Severity:** degradation

**Setup:**

Kohl has an editor open with an empty note

**Trigger:**

Kohl pastes a long markdown document (15,000 chars with headers, code blocks, lists) into the body. She clicks Save

**Expected:**

POST /api/notes succeeds with 201. Response includes the full body (not truncated). When Kohl reloads or fetches the note, the full body is returned. A markdown preview (if rendered) shows the full document

**Concern:**

If the body is truncated server-side or the database column is too small, Kohl loses content. If retrieval is slow for large bodies, she perceives the app as broken

**Property:**

Server accepts and persists bodies up to the contract limit (16384 chars); retrieval is fast enough for 15K body to feel instant

**Implies:**
- POST /api/notes validates body max 16384 chars (returns 422 if exceeded)
- SQLite TEXT column for body is large enough (TEXT is unbounded)
- GET /api/notes/{id} returns full body without pagination or truncation
