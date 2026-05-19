## Scenario: PUT /notes/{id} requires If-Match header; missing header is rejected with 400

**Severity:** breakage

**Setup:**
Note exists on server. A client (naive curl, missing frontend code, or test harness) sends a PUT request without the If-Match header.

**Trigger:**
PUT /notes/1 with request body {title: 'new', body: 'new'}, but no If-Match header in the HTTP request.

**Expected:**
Backend returns 400 Bad Request with detail: "If-Match header is required for PUT /api/notes/{id}". The note is NOT updated.

**Concern:**
If the backend silently accepts a PUT without If-Match and updates the note, collision detection is bypassed. A client bug (forgetting to send If-Match) becomes a silent data loss (user's local edits overwrite server state undetected).

**Property:**
For all PUT /notes/{id} requests, If-Match header must be present. If absent, the request is rejected with 400.

**Implies:**
- Implies FastAPI route handler checks for If-Match header presence before any database operation.
- Implies the 400 response includes a clear message so client developers know what they're missing.
- Implies test should verify that curl/requests without If-Match header fails with 400, not 200.

