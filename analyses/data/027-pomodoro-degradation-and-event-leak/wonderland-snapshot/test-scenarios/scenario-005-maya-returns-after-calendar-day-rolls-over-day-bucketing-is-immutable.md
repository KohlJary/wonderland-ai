## Scenario: Maya returns after calendar day rolls over—day-bucketing is immutable

**Severity:** silent-wrongness

**Setup:**

Maya creates a focus session at 23:55 on Day A. The session is pending, attributed to Day A in the database. She closes the app. 10 minutes pass and it is now 00:05 on Day B. Maya reopens the app and her session is restored from disk.

**Trigger:**

Maya closes and reopens the app after midnight, crossing a calendar boundary.

**Expected:**

Session remains attributed to Day A (the day it was created). Query for Day A sessions includes Maya's session. Query for Day B sessions does not include it. The app displays the session with its original context intact.

**Concern:**

The session's `createdAt` timestamp is on Day A, but if the app reloads the session and re-attributes it to the current calendar day (naive 'today'), it will move the session from Day A to Day B, orphaning it from the history Maya expects to see. This is silent wrongness: no error, no crash, just the session appearing in the wrong place in the history. The contract specifies that `createdAt` is ISO8601, but doesn't explicitly forbid re-attribution.

**Property:**

For all sessions with `createdAt` on Day X, querying sessions for Day X must include that session, regardless of how many calendar days have passed since it was created. The calendar day of a session is immutable and set at creation time.

**Implies:**

- Implies backend requirement: the date-bucketing logic must use the immutable `createdAt` field to determine which calendar day a session belongs to, not the current system date. The contract stores `createdAt`; the implementation must ensure query logic doesn't re-attribute based on the current date.
- Implies Kenji/Tweedledum backend responsibility to ensure the date-bucketing index is immutable and queries don't re-bucket existing sessions.
- Flag for Cat: is date-bucketing an architectural decision that needs to be named explicitly in the ADR, or is it implicit in "session record" via the contract?

