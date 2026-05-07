## Scenario: User has completed 5 focus sessions on Day A; midnight transitions to Day B; user starts focus session 6 on Day B

**Severity:** degradation

**Setup:**
It is 11:55 PM on Day A (e.g., 2024-01-15 23:55:00). User has completed 5 focus sessions earlier today. User starts session 6 with targetDuration=25 minutes. Real time is 23:55:00 on Day A.

**Trigger:**
Real time advances 5 minutes. It is now 12:00 AM on Day B (2024-01-16 00:00:00 in local timezone). Session 6 is still in progress (20 minutes remaining of its 25-minute countdown).

**Expected:**
Session 6's createdAt timestamp is Day A (2024-01-15, when it was created). The session completes at 12:20 AM on Day B (2024-01-16 00:20:00). When user queries today's sessions (on Day B), session 6 is NOT included in the count (it was created yesterday, on Day A, even though it completed today). When user queries Day A's sessions, session 6 IS included (createdAt determines day).

**Concern:**
The app likely queries 'today' using `new Date().getDate()` or similar local system date. The session's createdAt is stored (I assume) as ISO8601 timestamp. If there's ambiguity about which date to use (start date vs. end date), the session might be attributed to the wrong day. I also suspect the app caches 'today's' sessions before midnight and doesn't refresh on date change. The session will appear in today's view (cached) even though it's not actually part of today's count. When the user queries tomorrow (Day B) after midnight, the cache is invalidated, the app re-queries, and session 6 is missing (because createdAt is Day A). The user sees a discontinuity: session 6 was visible yesterday, then invisible today.

**Property:**
For all sessions: the session's day is determined by its createdAt timestamp (the date portion of the ISO8601 string, interpreted in the user's local timezone), not by when it completed or when it was last updated. A session created on Day A is on Day A for all subsequent queries, even if it completed on Day B. The bucketing is immutable and time-invariant.

**Implies:**
- Implies local timezone handling: createdAt must be stored in a way that preserves the local timezone context. Either store it in local TZ as ISO8601 (with +HH:MM offset), or store UTC and convert on the fly for day-bucketing. Be explicit about which. Flag for Tweedledum and Tweedledee.
- Implies cache invalidation: 'today's' sessions cache must be invalidated at midnight (or at least on date change). If the app is left open across midnight, the cache should refresh automatically or when the date changes. Flag for Tweedledee.
- Implies query contract: GET /sessions?fromDate=2024-01-15&toDate=2024-01-15 must return sessions where createdAt's date portion (in local TZ) is 2024-01-15, regardless of completionStatus or endTime. Flag for Tweedledum and contract review.
