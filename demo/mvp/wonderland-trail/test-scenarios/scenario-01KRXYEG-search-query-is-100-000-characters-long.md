## Scenario 213: Search query is 100,000 characters long

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB4X
**Severity:** degradation

**Setup:**

User (malicious or accidental) sends a query parameter that is 100KB of text.

**Trigger:**

GET /api/notes/search?q=[100KB of unicode]

**Expected:**

Endpoint returns 400 Bad Request with clear message, or silently caps query at reasonable length (e.g., 1000 chars) and searches that.

**Concern:**

No stated limit on query length in ticket. Unbounded string search on 100KB query will spike CPU and memory. If the web framework doesn't cap URL length, the database layer may hang.

**Property:**

For all query strings Q with len(Q) > reasonable_max, the endpoint must reject or truncate gracefully.
