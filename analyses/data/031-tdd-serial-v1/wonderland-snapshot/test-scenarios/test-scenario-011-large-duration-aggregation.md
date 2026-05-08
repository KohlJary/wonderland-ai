## Scenario: Daily aggregation handles very large duration values and high session counts

**Severity:** silent-wrongness

**Setup:**

A user (or a power user, or a test suite) logs sessions with very large durations or logs many sessions in a single day.

**Trigger:**

One of two scenarios:
1. A single session with very large duration_ms (e.g., 999999999 ms, approximately 11.5 days) is logged.
2. Many sessions (100+) are logged in a single day.

When daily review aggregates, it must SUM all durations and COUNT all sessions.

**Expected:**

The aggregation returns correct sums and counts without integer overflow. If using 32-bit integers, a SUM can overflow (e.g., INT32_MAX = 2^31 - 1 = 2147483647 ms ≈ 24.8 days). The backend must use 64-bit integers or check for overflow and return an error.

**Concern:**

If the backend uses 32-bit integers and a user logs sessions totaling more than ~24.8 days in a day (unrealistic but possible in test scenarios), the SUM will overflow and wrap around to a negative number or a small number. The daily review will display silently wrong stats: "You completed 5000 sessions today!" when it should show more. This is data corruption without error indication.

Similarly, high session counts can overflow a 32-bit integer COUNT if a user (or a malfunctioning client) logs 2+ billion sessions. While 2 billion is unrealistic per day, the backend should be robust.

**Property:**

For all sets of sessions S logged on a single day:
- total_focus_time_ms = SUM(duration_ms for s in S) must equal the true mathematical sum, not overflow
- completed_focus_count = COUNT(s in S) must equal the true count, not overflow

**Implies:**

- Implies schema: the SUM and COUNT aggregation functions must use 64-bit integers (BIGINT in SQL, i64 in Rust)
- Implies testing: test suite must verify aggregation with large individual durations and high session counts
- Implies robustness: if using a database that defaults to 32-bit, the schema must explicitly specify BIGINT for SUM/COUNT results

**Test Coverage:**

`tests/test_daily_review_fragility.py::TestLargeNumberHandling::test_large_duration_does_not_overflow_aggregation`

`tests/test_daily_review_fragility.py::TestLargeNumberHandling::test_many_sessions_do_not_overflow_count_aggregation`
