## Test Scenario: Dev Reviews Today's Completed Sessions

**Severity:** breakage (if this fails, the reflection moment is lost)

**Setup:**

Dev is a 26-year-old engineer who uses pomodoro for self-awareness. He has completed 8 focus sessions today (over 3 hours of focused work). He opens the app at the end of the day.

**Trigger:**

Dev opens the app and expects to see today's summary immediately on the landing view. He then taps to see the list of individual sessions.

**Expected:**

1. GET /sessions/today returns HTTP 200
2. Response includes summary with count=8, total_seconds >= 8*1500 (at least 3 hours)
3. Response includes sessions array with 8 entries, ordered by start_time descending
4. Each session has id, start_time, end_time, duration_seconds, is_completed=true
5. The timestamps are in ISO8601 format
6. All sessions are owned by the authenticated user (implicit multi-user safety check)

**Concern:**

The concern is that:
- Active sessions might be included in the count (they shouldn't be)
- Sessions from yesterday might be included (timezone boundary issue)
- The timestamps might be malformed or inconsistent between responses
- The total_seconds might be computed incorrectly (truncation, rounding, or arithmetic errors)
- Large result sets (50+ sessions) might cause timeouts or memory issues

**Property:**

For all users U and completed sessions S in U's history today:
- GET /sessions/today returns all S where is_completed=true and DATE(created_at) = TODAY
- All S in response have is_active=false
- summary.count = count of returned sessions
- summary.total_seconds = SUM of (end_time - start_time) for all S

**Implies:**

- Implies GET /sessions/today endpoint
- Implies filtering by user_id, date (created_at), and is_completed=true
- Implies correct timestamp generation and timezone handling
