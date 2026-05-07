## Test Scenario: Session completion in-flight while history query executes

**Severity:** silent-wrongness

**Feature:** Feature-001 & Feature-002 (cross-domain)

**Setup:**

User has completed 3 focus sessions today (recorded). Session #4 is just completed. Frontend POSTs the completion event to `/sessions/complete` (request in flight, not yet ACK'd). Simultaneously, user taps "History" and frontend queries GET `/sessions?window=today`.

**Trigger:**

Two concurrent requests:
1. POST /sessions/complete (for session #4, started 30 seconds ago, takes 100ms to process)
2. GET /sessions?window=today (query fires 50ms after POST, while #1 is still being written to DB)

**Expected:**

The GET response is consistent with one of two states:
- A: Backend has committed session #4 to DB; GET returns 4 sessions
- B: Backend has not yet committed session #4; GET returns 3 sessions

The inconsistency happens if the GET response returns *some* fields from session #4 (e.g., session_count=4 but sessions list has 3 items) or if the aggregates are stale.

**Concern:**

Race condition between concurrent POST (write) and GET (read). Backend may return a response that mixes committed and uncommitted data:
- session_count=4 (counted the in-flight record)
- sessions=[3 records] (committed records only)
- total_focus_seconds=stale (counted wrong number of sessions)

This is silent wrongness: the response looks plausible (numbers are positive, session_id values are valid UUIDs) but is internally inconsistent and misleading.

**Property:**

For all concurrent POST (session completion) + GET (history query) pairs:
- session_count must equal len(sessions)
- total_focus_seconds must equal sum of focus_duration_seconds for all sessions in the list
- window_start and window_end must correctly bracket all returned sessions

**Mechanism:**

Backend must isolate reads and writes. Options:
1. Row-level locking: POST acquires write lock on sessions table; GET waits
2. Snapshot isolation: GET reads a consistent snapshot of the DB at a specific transaction timestamp; POST writes to a new snapshot
3. Optimistic retry: GET is fast and reads whatever's available; if inconsistency detected on next refresh, re-query

For a high-consistency system, option 1 or 2 is standard.

**Implies:**

- Architectural question for Cat: does the system guarantee read-your-writes consistency for the same user's queries? If not, frontend must be defensive about stale history display.
- Feature-002's contract may need to specify: "History queries are eventually consistent (may lag session completion POSTs by <N> seconds)" or "are strongly consistent (immediate)."

**Runnable Test:**

- `tests/test_concurrent_session_write_history_read.py::test_session_completion_and_history_query_are_consistent`
