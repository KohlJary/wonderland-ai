## Scenario: Range query for 1000+ sessions responds in <2 seconds without memory spike

**Severity:** degradation

**Setup:**

Historical data: 2000 completed sessions from a full year of pomodoro work. User queries `GET /sessions/range?start_date=2023-01-01&end_date=2024-01-01` with pagination enabled (`limit=500`, defaulting to page 1).

**Trigger:**

`GET /sessions/range` for a full year (1000s of sessions) with default pagination.

**Expected:**

Response includes the first 500 sessions, with pagination metadata (`page=1, limit=500, count=2000`). Response time is <2 seconds. Backend memory usage doesn't spike beyond nominal levels (same memory as a 500-session response).

**Concern:**

Backend may load all 2000 sessions into memory before paginating, causing a memory spike. SQLAlchemy's lazy-loading behavior may also cause N+1 query problems if each session's properties trigger additional database queries. Result: slow endpoint that gets slower as history grows, potential OOM on shared infrastructure or resource-constrained devices.

The test files Tweedledee wrote include `test_large_date_range_doesnt_timeout`, but it only creates 20 sessions. That test will pass even if the backend loads all rows; a true stress test needs realistic scale.

**Property:**

For all queries Q with N matching sessions and a limit parameter L:
- Response time is O(L), not O(N). The backend must not load or process rows beyond the limit.
- Memory footprint during query is O(L), not O(N).

**Implies:**

- Implies backend must use database-level `OFFSET` and `LIMIT` at query time, not application-level slicing after fetching all rows.
- Implies SQLAlchemy query must not trigger N+1 loads (e.g., accessing session.end_time on 500 rows shouldn't issue 500 additional queries).
- Implies test harness needs ability to seed large datasets (e.g., factory fixtures that create 2000 sessions without timeout) and measure timing/memory. Current test suite does not include performance benchmarks.
- Consider pytest-benchmark or memory_profiler for instrumentation.
