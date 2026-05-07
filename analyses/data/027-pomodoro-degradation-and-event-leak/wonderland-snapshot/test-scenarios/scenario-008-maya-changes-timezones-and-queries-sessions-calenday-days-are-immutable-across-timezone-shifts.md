## Scenario: Maya changes timezones and queries sessions—calendar days are immutable across timezone shifts

**Severity:** degradation

**Setup:**

Maya lives in Pacific Time. She creates sessions on Day A (UTC−8). The sessions' `startTime` timestamps are stored in ISO8601 (e.g., `2024-01-15T23:30:00−08:00` for 11:30 PM PT). She then travels to Eastern Time (UTC−5) and reopens the app. She queries sessions from Day A to Day C using the same calendar dates she used before. The backend's date-bucketing logic still assumes Pacific Time, or worse, doesn't normalize timezones at all.

**Trigger:**

Maya changes timezones and queries sessions from her new timezone.

**Expected:**

The query returns the same sessions that would have been returned from Pacific Time, despite the timezone change. The calendar dates she uses for the query are still her local calendar dates (what she sees on her wall calendar), and the results should match.

**Concern:**

The contract specifies that `createdAt` is ISO8601, which includes timezone info. But the query endpoint takes `fromDate` and `toDate` as date strings (implicitly local to the client's current timezone). If the backend doesn't normalize both the session's date and the query's date to the same reference frame (e.g., UTC), a timezone change can cause sessions to appear in the wrong date bucket. Specifically: if Maya's session was created at 23:30 Pacific (which is 07:30 UTC on the next calendar day), and the backend naively buckets it by "day of the UTC timestamp," it lands in UTC Day+1. When Maya queries from Eastern Time (also UTC-based), the same bucket applies, and the session appears in the wrong local date. This is degradation (the system doesn't crash, but returns fewer or more results than expected) rather than breakage, because the user can work around it by adjusting query dates.

**Property:**

For all sessions with `startTime` T in timezone Z, and a query for dates D1 to D2 in timezone Z', the session must appear in the query results if and only if the session's local date in Z' falls within [D1, D2], regardless of Z. The calendar day must be immutable across timezone changes (each user's calendar day is relative to their local time).

**Implies:**

- Implies backend requirement: date-bucketing logic must convert both session timestamps and query dates to a canonical timezone (UTC, or the session's original local timezone) before comparing buckets, then convert back to the user's local timezone for display. Current contract doesn't specify this, and the query endpoint shape (date strings without timezone) doesn't make it obvious.
- Implies Kenji/Tweedledum backend responsibility to implement timezone-aware date bucketing. The session's `startTime` already includes timezone; the query endpoint must also accept timezone info (either from headers or query params) to do this correctly.
- Flag for Cat: the query endpoint needs design clarity. Currently it takes `fromDate` and `toDate` as strings; should it also take a timezone? Or should it always use UTC and let the client handle local conversion?

