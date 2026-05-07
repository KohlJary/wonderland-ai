## Scenario 008: Yuki's sessions get bucketed into the wrong week because backend groups by UTC date while Yuki is in a timezone east of UTC

**Severity:** silent-wrongness

**Setup:**

Yuki is in Tokyo (UTC+9). She completes a session at 11:30 PM Tokyo time. The backend stores the session's completed_at as a Unix timestamp. She views her weekly history.

**Trigger:**

The backend aggregates sessions by UTC calendar date (not local date). A session completed at 11:30 PM Tokyo time is stored with a completed_at timestamp that, when converted to UTC, falls on the previous calendar day.

**Expected:**

Yuki's session appears in the correct week (the week containing her local calendar date). The weekly aggregates show the session counted on the day she completed it (Thursday, in her local time), not the day it appears in UTC (Wednesday).

**Concern:**

The backend uses UTC date binning without applying the user's timezone offset. A session completed at 2024-01-12 01:00 JST becomes 2024-01-11 16:00 UTC and gets binned as 2024-01-11—wrong week. Yuki sees her Thursday sessions appear in Wednesday's bucket, confusing her trend analysis. This is silent-wrongness because the data is recorded but in the wrong place, and Yuki might not notice until she looks closely at the dates. The contract specifies UTC v1 limitation, but the failure mode shows the cost when Yuki inevitably uses it from a non-UTC timezone.

**Property:**

For all sessions S with local_date = D (user's local calendar date) and timezone = TZ, the session appears in the weekly/daily aggregates under D, not under a different date caused by UTC conversion.

**Implies:**
- Requires timezone handling at the backend—contract specifies UTC v1 assumption, but the failure mode shows it breaks in non-UTC locales.
- May require design decision: store completed_at in user's local timezone, or store UTC and convert on read. Flag for Cat.
