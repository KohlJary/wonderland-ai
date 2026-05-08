## Scenario 021: Dmitri opens daily review and sees completed focus sessions from today with accurate aggregates

**Severity:** breakage

**Setup:**

Dmitri has completed 6 focus sessions today (25 min each, 3 of them actually ran to completion, 2 paused-then-resumed completing the full 25 min, 1 completed early at 20 min). He also has 4 break sessions completed (5 min each). He opened the app; the daily review view is visible. The current time is 16:00 UTC.

**Trigger:**

Dmitri views the daily summary on the home screen (or taps one button to see it). The view fetches GET /sessions?date=2024-01-15 (today's UTC date).

**Expected:**

The response includes all six completed focus sessions and four completed breaks in the array. The frontend calculates and displays: 'Completed focus sessions: 6', 'Total focus time: 145 minutes', 'Breaks taken: 4'. Each session shows its type (focus/break), timestamp, and actual duration.

**Concern:**

The backend query might not filter correctly to today's date (returning yesterday's sessions or tomorrow's). The aggregates might miscalculate (summing configured_duration instead of actual_duration). Abandoned sessions (paused and never resumed) might leak into the count. The timezone interpretation might be off — a session completed at 23:55 UTC might be counted as yesterday if the user's local date is different.

**Property:**

For any date D and user U, GET /sessions?date=D returns all and only sessions where completed_at falls within [D 00:00 UTC, D 23:59:59 UTC) and status='completed'. Frontend sum(duration_actual_seconds for each session) equals displayed total focus time.

**Implies:**
- Implies contract clarification on what happens if the date param is malformed (e.g., ?date=invalid) — should return 400 or 200 with empty array?
- Implies backend must filter sessions by completion status before returning — abandoned or paused sessions must not appear.
