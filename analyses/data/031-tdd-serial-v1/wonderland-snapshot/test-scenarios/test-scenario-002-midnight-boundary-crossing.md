## Scenario: User completes sessions across midnight boundary with timezone offset

**Severity:** silent-wrongness

**Setup:**

User is in Pacific Time (PT, UTC-8). At 11:55pm PT on Monday, December 10th:
- User has completed 2 focus sessions (50 min total) on Monday
- User is in the middle of a third focus session that will complete at 12:05am Tuesday

The session started at 11:50pm Monday PT. Its timer will reach completion at 12:15am Tuesday PT (25 minutes from start).

**Trigger:**

User views daily review on Monday evening (before midnight).
Expected: 2 sessions, 50 min.

Then user views daily review on Tuesday morning.

**Expected:**

Monday daily review: 2 completed sessions, 50 min
Tuesday daily review: 1 completed session (the one that finished after midnight), plus whatever sessions started Tuesday morning

The session that *completed* after midnight belongs to Tuesday's count, even though it *started* on Monday.

**Concern:**

Timezone mishandling is silent — the UI will cheerfully display stats that are off by one or belong to the wrong day. The backend must use the *user's local timezone* to determine midnight, not UTC. If the backend defaults to UTC, a PT user's stats will be 8 hours off. The frontend must send the user's timezone offset when querying.

Also: if the backend doesn't track session completion time separately from session start time, it can't distinguish "which day did this session complete on?"

**Property:**

For all sessions S with start_time T1 and end_time T2:
- daily_review(day D) includes S if and only if (midnight(D) <= T2 < midnight(D+1)) in user's local timezone
- Corollary: a session started on day D-1 can belong to day D's stats if it completes after midnight(D)

**Implies:**

- Implies contract requirement: session event log must record completion_time separately from start_time
- Implies frontend contract: daily-review request must include user_timezone (e.g., "America/Los_Angeles")
- Implies backend implementation: query uses user's timezone offset to calculate midnight boundaries, not UTC
