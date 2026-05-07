## Scenario 009: Priya views weekly and all-time session statistics

**Severity:** degradation

**Setup:**

Priya has 47 sessions over 3 months. All persisted with completed_at timestamps.

**Trigger:**

Frontend GETs /sessions/stats?period=week. Then GETs /sessions/stats?period=all_time.

**Expected:**

Week: returns stats for last 7 days. All-time: stats for full history.

**Concern:**

Stats endpoint structure undefined in contract. Response shape not finalized.

**Property:**

GET /sessions/stats?period=week|all_time returns valid aggregated response.

**Implies:**
- Test file: tests/test_session_history.py
- Implies backend supports aggregation queries.
