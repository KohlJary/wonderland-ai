## Scenario 348: Client sends PUT without If-Match header, request is rejected with 400 Bad Request

**GUID:** 01KRY1DY1PSMHZM094C8W7E46N
**Severity:** breakage

**Setup:**

Note exists on server. A client sends PUT without If-Match header (e.g., a naive curl command, or frontend bug).

**Trigger:**

PUT /notes/1 with request body {title: 'new', body: 'new'}, no If-Match header.

**Expected:**

Backend returns 400 Bad Request with detail like 'If-Match header is required for PUT /notes/{id}'. The note is NOT updated.

**Concern:**

If missing If-Match is silently accepted, a client bug bypasses collision detection entirely, causing silent overwrites.

**Property:**

For all PUT /notes/{id} requests, If-Match header is required. Missing header causes 400 rejection.
