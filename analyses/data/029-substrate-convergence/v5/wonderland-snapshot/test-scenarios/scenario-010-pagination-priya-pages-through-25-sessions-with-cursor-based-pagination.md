## Scenario 010: Pagination: Priya pages through 25 sessions with cursor-based pagination

**Severity:** silent-wrongness

**Setup:**

Priya has 25 sessions. Frontend requests first page with limit=10.

**Trigger:**

Frontend GETs /sessions?limit=10. Backend returns 10 records + next_cursor. Frontend GETs /sessions?cursor=<token>&limit=10 (repeat).

**Expected:**

Each page returns 10 records in descending order by started_at. All 25 reachable in 3 pages. No duplicates.

**Concern:**

Cursor tokens must be robust across time and backend restarts. Offset-based pagination would fail.

**Property:**

For all valid cursor tokens, GET /sessions?cursor=X returns next batch with no duplicates.

**Implies:**
- Test file: tests/test_session_history.py
