## Scenario 029: User in PT (UTC-8) completes session 23:59 PT Monday, credited to Monday not Tuesday

**Severity:** silent-wrongness

**Setup:**

Derek in PT has streak. Monday 23:59 PT: completes session (hits goal). Backend logs: 2024-01-02T07:59:00Z (Tue UTC). Streak query must convert UTC→PT before grouping by date.

**Trigger:**

Streak query for 'Monday PT' executes. Backend must convert UTC timestamp to PT date, not use UTC date.

**Expected:**

Session credited to Monday PT (Derek's calendar day). Monday streak ≥3 (goal hit). Streak does NOT break.

**Concern:**

If backend queries 'Jan 2 UTC', it won't find this session (it's Jan 2 UTC but Jan 1 PT). Monday PT seen as 0 sessions, chain breaks. Silent wrongness: Derek hit goal but streak resets without warning.

**Property:**

streak_for_day(local_date) = sum(sessions where to_user_tz(session.completed_at).date() == local_date).

**Implies:**
- Implies Feature 004: store user's timezone (e.g., America/Los_Angeles)
- Implies Feature 003: timestamp in UTC (unambiguous at storage)
- Implies Feature 005: backend streak query loads user timezone, converts UTC→local before grouping
- Implies test fixture: inject sessions with explicit timestamps + user timezone
