## Scenario: Query with boundary dates uses inclusive-inclusive boundaries at midnight

**Severity:** degradation

**Setup:**
User completes sessions across three calendar days. Sessions created at:
- 2024-01-15 23:00 (11 PM on day 15)
- 2024-01-16 00:30 (12:30 AM on day 16, just after midnight)
- 2024-01-16 14:00 (2 PM on day 16)
- 2024-01-17 01:00 (1 AM on day 17)

User queries GET /sessions?fromDate=2024-01-16&toDate=2024-01-16 (single day query for calendar day 16).

**Expected:**
The query returns sessions 2, 3 only (the two sessions created on calendar day 2024-01-16). Sessions 1 and 4 are not included.

The fromDate and toDate boundaries are interpreted as *calendar dates* in the user's local timezone, not precise wall-clock times. Semantically, the query means "give me all sessions created on this calendar day" (from 00:00:00 to 23:59:59 local time on that date).

**Concern:**
The backend might interpret the date boundaries as precise wall-clock times:
- fromDate='2024-01-16' is treated as '2024-01-16T00:00:00 UTC' (the instant of midnight UTC)
- toDate='2024-01-16' is treated as '2024-01-16T00:00:00 UTC' (the same instant)
- The range [00:00 UTC, 00:00 UTC) is empty, so no sessions are returned

Or the backend might interpret toDate as exclusive (a common off-by-one in date ranges):
- fromDate='2024-01-16' is '2024-01-16T00:00:00 UTC'
- toDate='2024-01-16' is treated as exclusive, so the range is [00:00, 00:00) = empty

Or the backend might not account for timezones at all and do all date math in UTC, so a session created at 11 PM PT (3 AM UTC next day) gets bucketed to the wrong calendar day.

The degradation: the user sees zero sessions for a day they worked, or they see sessions from the wrong day. It's not a crash, but it's wrong.

**Property:**
For all date-range queries with fromDate and toDate:
- If fromDate and toDate are the same calendar date (in local TZ), the range includes all sessions created on that calendar date (from 00:00:00 to 23:59:59:999 local time)
- The boundaries are inclusive-inclusive (both ends are included)
- Timezone is the user's local timezone, not UTC
- createdAt timestamps are stored as UTC or epoch, and are converted to local TZ for comparison

More formally: 
- fromDate='YYYY-MM-DD' is converted to 'YYYY-MM-DDTXX:XX:XX' (midnight in local TZ) → converted to UTC for storage comparison
- toDate='YYYY-MM-DD' is converted to 'YYYY-MM-DD T23:59:59.999' (end of day in local TZ) → converted to UTC for storage comparison
- Sessions with createdAt in [UTC_fromDate, UTC_toDate] are included

**Implies:**
- Implies query parsing: fromDate and toDate need to be converted from calendar-date strings to timezone-aware boundaries before querying. Flag for Tweedledum.
- Implies timezone awareness: the backend needs to know the user's timezone (stored in user preferences or inferred from device/request headers) to correctly compute boundaries. Flag for Tweedledum and contract review.
- Implies test data: tests need to verify behavior at day boundaries, especially with timezone mismatches (e.g., a session created at 11 PM in one timezone is 3 AM UTC, which is the next calendar day in UTC but the same calendar day locally). Flag for test harness.
- Implies edge case: what if user's timezone is not set or invalid? Fallback to UTC? Ask the user? Flag for Cat to include in handling-missing-data discussion.
