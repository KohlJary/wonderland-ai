## Scenario 006: Range query for 1000+ sessions responds in <2 seconds without memory spike; uses database pagination, not app-level slicing

**Severity:** degradation

**Setup:**

Historical data: 2000 completed sessions over a year. Query GET /sessions/range?start_date=2023-01-01&end_date=2024-01-01&limit=500.

**Trigger:**

Large date range returning thousands of matching sessions; must paginate efficiently.

**Expected:**

Response time <2 seconds. Memory footprint is O(limit), not O(total_matching). First 500 sessions returned with pagination metadata (count=2000, page=1).

**Concern:**

Backend may load all 2000 sessions into memory before paginating, causing memory spike and slow response. SQLAlchemy N+1 queries may occur if session properties are lazy-loaded.

**Property:**

For all queries Q with N matching sessions and limit L, response time is O(L), not O(N). Memory footprint is O(L), not O(N).

**Implies:**
- Implies backend must use database OFFSET/LIMIT in query itself, not application-level slicing after fetching all rows.
- Implies test harness needs ability to seed large datasets (factories creating 2000 sessions) and measure timing/memory (pytest-benchmark, memory_profiler).
