## Test Scenario 018: Paused time is excluded from daily focus minute total

**Severity:** degradation

**Feature:** Feature 002: Review today's session count

**Setup:**

Maya completes a session that nominally takes 25 minutes. However, she pauses for 5 minutes during the session to take a call. The wall-clock duration is 30 minutes, but the actual focus time is 25 minutes (paused_duration_ms = 5 × 60 × 1000).

The SessionRecord is written with:
- session_duration_ms = 25 × 60 × 1000 (excluding pause time, as per contract)
- session_type = 'focus'

**Trigger:**

Maya checks her "Today" view. The app fetches GET /api/session-counts/today.

**Expected:**

The total_focus_minutes should be 25 (the actual focused time), not 30 (the wall-clock time). The count should be 1 (she ran one session, even though it had a pause in it).

**Concern:**

If the backend stores session_duration_ms without excluding pause time, or if the historical aggregation sums paused_duration_ms alongside session_duration_ms, the total will be inflated. Over a week, a user with multiple pauses could see their total focus time overstated by 10-20 minutes.

This is a degradation (not breakage) because the app still functions, but the metric is wrong.

**Property:**

For all sessions with pauses:
  session_duration_ms_in_record = wall_clock_duration - paused_duration_ms

And for daily aggregations:
  daily_total_focus_minutes = sum(session_duration_ms) / 60000 (in minutes)

Paused time is never included in the daily total.

**Implies:**

This tests the session_duration_ms calculation in Feature 001 (contract-note-003) and the aggregation query in Feature 002 (contract-note-004). The two features must align on what "focus time" means.

