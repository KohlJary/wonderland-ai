## Scenario 062: Getting all notes when the database has thousands of notes

**GUID:** 01KRXTD96CAEAJCAJEH0RQWM06
**Severity:** degradation

**Setup:**

Database contains 10,000 notes with 2-5 tags each. GET /api/notes with no pagination, filtering, or limit.

**Trigger:**

GET /api/notes.

**Expected:**

Returns all notes in reverse chronological order. Response size: ~5MB+ JSON. Memory usage on server: all notes and all tags loaded into memory simultaneously.

**Concern:**

The code does: db.query(Note).order_by(Note.updated_at.desc()).all(). No pagination, no limit. For an MVP this is acceptable, but the moment a user accumulates real data, the endpoint becomes slow and memory-hungry. Also, the response may exceed browser JSON parse limits (typical timeout at >50MB).

**Property:**

For all databases D with N notes, the response time to GET /api/notes is O(N) in both memory and latency.

**Implies:**
- Known MVP limitation — pagination and filtering are not in v1 scope per ticket. This is acceptable for MVP but flagged as a known risk at scale. Fast-follow: add limit/offset pagination and filtering by tag/date.
