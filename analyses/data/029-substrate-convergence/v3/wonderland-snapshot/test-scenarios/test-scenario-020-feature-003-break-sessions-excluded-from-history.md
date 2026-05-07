## Test Scenario 020: Break sessions are excluded from historical aggregations

**Severity:** silent-wrongness

**Feature:** Feature 003: Inspect historical session data across weeks and all-time

**Setup:**

Yuki has completed 4 focus sessions and 4 break sessions over two days. Each focus session is 25 minutes; each break is 5 minutes. The SessionRecords in the DB are:
- 4 records with session_type='focus', session_duration=25 minutes each
- 4 records with session_type='break', session_duration=5 minutes each

**Trigger:**

Yuki opens the "This Week" view and fetches GET /api/session-history/weekly.

**Expected:**

The response should show:
- session_count = 4 (focus sessions only)
- total_focus_duration_minutes = 100 (4 × 25)
- break_duration_minutes = 20 (4 × 5)

The break_duration_minutes field should be included in the response (for potential UI display), but the session_count should count focus sessions only.

**Concern:**

If the backend doesn't filter by session_type when calculating session_count, the count will be 8 (4 focus + 4 break). The user will think they completed 8 sessions when they really completed 4. Over time, this makes the weekly view useless as a metric of productivity.

The concern is compounded if the contract doesn't specify whether break_duration should be in the response at all. If the backend includes break_duration but the frontend doesn't display it, the data is unused. If the frontend expects it but the backend doesn't provide it, the response shape breaks.

**Property:**

For all aggregations (weekly, all-time):
- session_count includes only SessionRecords where session_type='focus'
- total_focus_duration_minutes sums session_duration_ms only for session_type='focus' records
- break_duration_minutes sums session_duration_ms only for session_type='break' records (included in response for potential UI use)

**Implies:**

This tests the filtering and aggregation logic across the historical queries (contract-note-006). The scenario validates that the backend correctly distinguishes focus from break, consistent with Feature 002.

