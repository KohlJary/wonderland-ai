# Test Scenario 005: Today's session count includes focus sessions only, not breaks

**Severity:** silent-wrongness

**Setup:**

Priya has completed a pomodoro cycle today: 2 focus sessions (25 min each) and 2 breaks (5 min each). All are recorded in SessionRecord. She opens the app and views the main screen, which shows today's session count.

**Trigger:**

GET /api/session-counts/today is called.

**Expected:**

The displayed count is "2 sessions" (only the two focus sessions). The two breaks are not included in the count.

**Concern:**

If the query doesn't filter by session_type:
- The count is "4" (includes breaks).
- Priya sees 4 sessions, but when she reviews her history, she only sees 2 focus sessions (because the history view correctly filters).
- Priya is confused: "Why does the main screen show 4 but the history shows 2?"

This is a silent wrongness: the feature doesn't crash, but the two numbers don't match, and the user metric is wrong.

**Property:**

For all times T within the user's local date:
- count(today) = count of SessionRecords where session_type='focus' AND completed_at in [T_start, T_end].
- Breaks (session_type='break') are excluded from the count.
- The count on the main screen matches the session_count returned by /api/session-history/weekly for today.

**Implies:**

- Implies filtering by session_type='focus' in the today-count query — flag for Tweedledum.
- Implies session_type field exists on SessionRecord with correct values — flag for Tweedledum.
