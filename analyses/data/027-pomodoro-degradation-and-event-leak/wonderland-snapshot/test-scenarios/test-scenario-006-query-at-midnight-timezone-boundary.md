## Scenario: User queries "today's sessions" exactly at timezone boundary

**Severity:** silent-wrongness

**Setup:**
A focus session is created at 11:55 PM PT (Pacific) on calendar day 2024-01-15. The session is still in progress (20 minutes elapsed, 5 remaining). Real time is now 12:05 AM ET (Eastern) on calendar day 2024-01-16 — but only 9:05 PM PT on calendar day 2024-01-15. User's device timezone is set to ET.

**Trigger:**
User navigates to "Today" view on the device (showing 2024-01-16 in ET timezone). The app issues GET /sessions?fromDate=2024-01-16&toDate=2024-01-16 to retrieve "today's sessions".

**Expected:**
The session created at 11:55 PM PT (which is 2024-01-15 in PT, the user's *original* timezone) is NOT included in the result. The session is still attributed to 2024-01-15 (PT), not re-bucketed to 2024-01-16 (ET) based on current timezone.

When the user navigates to "Yesterday" (2024-01-15 in ET, which is 23 hours and 50 minutes in PT), or queries explicitly ?fromDate=2024-01-15&toDate=2024-01-15, the session IS included.

**Concern:**
The app uses `new Date().toLocaleDateString()` or similar to bucket sessions by calendar day. When the timezone changes, the same createdAt timestamp might be re-bucketed to a different calendar day. A session with createdAt='2024-01-16T04:55:00Z' (UTC) is:
- 2024-01-15 in PT (UTC-8)
- 2024-01-16 in ET (UTC-5)

If the app bucketed the session by the user's *current* timezone instead of the timezone when it was created, a session initially filed under 2024-01-15 (PT) would mysteriously appear under 2024-01-16 when timezone changes to ET. Or if the app cached the bucketed date and then changed timezone, the cache becomes stale.

The silent wrongness: the user looks at "Today" and doesn't see a session they *just* created 10 minutes ago. Or the user sees sessions on "Today" that shouldn't be there. Or the same session appears on two different calendar days depending on timezone.

**Property:**
For all sessions: createdAt is stored as an absolute timestamp (ISO8601 UTC or epoch). Day-bucketing is computed as: date in user's *local* timezone. When timezone changes, day-bucketing is recalculated on-the-fly (not cached). A session's calendar day is immutable relative to the timezone the user was in when the session was created — OR, more robustly, sessions are bucketed by the wall-clock date when they were created, and timezone is only a display concern.

**Implies:**
- Implies timestamp storage: createdAt must be in UTC (not local TZ), so re-bucketing always works correctly. Flag for Tweedledum.
- Implies query semantics: GET /sessions?fromDate=2024-01-15&toDate=2024-01-15 interprets dates as user's *current* local timezone. So if the user is in PT and queries for 2024-01-15, it returns sessions with createdAt in [2024-01-15T00:00:00 PT, 2024-01-16T00:00:00 PT) in UTC, which is [2024-01-15T08:00:00 UTC, 2024-01-16T08:00:00 UTC). If the timezone changes, the same query now returns different results. This is correct but worth pinning explicitly. Flag for contract review.
- Implies frontend state: if the app has cached "today's sessions", the cache must be invalidated when timezone changes. Flag for Tweedledee.
