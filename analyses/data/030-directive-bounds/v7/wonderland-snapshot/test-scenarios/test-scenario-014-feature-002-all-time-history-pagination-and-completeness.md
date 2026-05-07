## Test Scenario: All-time history with 1000+ sessions across multiple years

**Severity:** degradation

**Feature:** Feature-002 (history queries & pagination)

**Setup:**

Jordan (productivity tracker persona) has been using the app for 2 years. Total sessions recorded: 1,247 (roughly 600+ per year). Jordan queries GET `/sessions?window=all-time` to review total productivity over time.

**Trigger:**

Fetch all-time history for a user with 1,247 completed sessions spread across 104 weeks (2 years).

**Expected:**

Response includes all 1,247 sessions with correct aggregates:
- session_count = 1,247
- total_focus_seconds = sum of all focus sessions (approx. 800+ hours of tracked work)
- window_start = date of first session ever
- window_end = current time
- sessions list contains all records (or properly paginated if pagination is supported)

**Concern:**

Large history queries can reveal:
1. **Truncation:** Backend times out or hits a result-size limit, returning only the first 100 sessions. User sees incomplete history.
2. **Memory pressure:** Fetching 1,247 sessions into memory and serializing to JSON causes OOM or delays.
3. **Database query performance:** Scanning 1,247 rows without proper indexing is slow (seconds of latency, timeout).
4. **Aggregate calculation correctness:** Summing 1,247 focus_duration_seconds values is error-prone (integer overflow, floating-point rounding).
5. **Pagination bug:** All-time window is paginated (e.g., limit=100, offset=0), but offset logic is wrong — some sessions are skipped or duplicated.

**Property:**

For any user history query (window=today, week, all-time):
- session_count == len(sessions)
- total_focus_seconds == sum(s.focus_duration_seconds for s in sessions if s.session_type == 'focus')
- No sessions in the response list are duplicated
- All sessions within the window boundary (window_start <= completed_at <= window_end) are included

For all-time windows specifically:
- Response time < 5 seconds (even for 1,000+ sessions)
- No timeout or truncation errors

**Mechanism:**

Backend should:
1. Use database indexing on (user_id, completed_at) for fast filtering
2. Implement pagination with limit/offset for all-time queries (e.g., return 100 at a time, allow caller to fetch more)
3. Pre-aggregate totals in a summary query, not by iterating the result set in application code
4. Use integer arithmetic for all duration sums (no floats)
5. Validate offset+limit doesn't exceed total count (prevent off-by-one on last page)

**Implies:**

- Contract clarification for Feature-002: should all-time be paginated? If yes, contract needs to specify limit/offset parameter handling.
- Performance test: response time SLA for large histories (not just correctness, but also latency)
- Dormouse (SRE) should monitor: query latency on /sessions?window=all-time for users with large histories

**Runnable Test:**

- `tests/test_feature_002_large_history_completeness.py::test_all_time_window_returns_all_sessions_with_1000_plus_records`
- `tests/test_feature_002_large_history_completeness.py::test_aggregates_correct_with_large_session_count`
- `tests/test_feature_002_large_history_completeness.py::test_all_time_query_completes_in_reasonable_time`
