## Test Scenario 017: Break sessions are not counted in today's focus session count

**Severity:** silent-wrongness

**Feature:** Feature 002: Review today's session count

**Setup:**

Marcus completes a 25-minute focus session. A SessionRecord is written with session_type='focus'. He then takes his 5-minute break. After the break completes, a second SessionRecord is written with session_type='break'.

**Trigger:**

Marcus checks his "Today" view to see how many focus sessions he's completed. The app fetches GET /api/session-counts/today.

**Expected:**

The count should be 1 (one focus session), not 2. The total_focus_minutes should reflect only the focus session (25 minutes), not the break (5 minutes).

The SessionRecord with session_type='break' should not be included in the count or the total_focus_minutes aggregation.

**Concern:**

If the backend doesn't filter by session_type='focus' when querying SessionRecords, the count will include break sessions. Over a day, if Marcus takes 4 sessions + 4 breaks, the count will show 8 instead of 4. The user will think they focused more than they actually did.

Additionally, total_focus_minutes might sum the break durations, making it even more incorrect.

**Property:**

For all queries of daily_count and daily_total_minutes, only SessionRecords with session_type='focus' are included. SessionRecords with session_type='break' are excluded.

**Implies:**

This tests the filtering logic in the daily count query (contract-note-004). The scenario validates that the backend correctly distinguishes focus from break when aggregating history.

