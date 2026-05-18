## Scenario 216: Search results exceed 10,000 matches on a single query

**GUID:** 01KRXYEG9WMJ0GPZ2FAHJSYB50
**Severity:** degradation

**Setup:**

Database has 50,000 notes; user searches for common word like 'the' that appears in 15,000 notes.

**Trigger:**

GET /api/notes/search?q=the

**Expected:**

Endpoint returns 15,000 results (or paginated subset with pagination token), or returns 200 with a subset and clear message that results are truncated.

**Concern:**

Ticket acceptance says 'endpoint returns JSON array of matching notes' but does not specify max result count. Returning 15,000 JSON objects will be a large payload (likely >10MB), slow to serialize, and slow for frontend to render. Response may time out or crash the browser.

**Property:**

For all queries Q that match N notes where N >> reasonable_render_count, the endpoint must either paginate or truncate with a clear signal.

**Implies:**
- Implies architectural decision about pagination — flag for Cat if not already designed.
