## Scenario 004: Historical query across DST boundary returns correct count despite timezone shift

**Severity:** silent-wrongness

**Setup:**

User in America/Los_Angeles. Sessions completed on DST end day (Nov 2024): one at 10 AM PDT, one at 1 AM PST (after shift). Query GET /sessions/range?start_date=2024-11-02&end_date=2024-11-02.

**Trigger:**

Date-range query crossing timezone fold (local 1:59:59 becomes 0:59:59).

**Expected:**

Response includes both sessions. DST boundary is handled correctly; no sessions dropped due to timezone misunderstanding.

**Concern:**

Timezone handling in date-boundary logic is fragile. Backend may use naive local-date calculation without accounting for UTC offset shift on DST boundaries, filtering sessions near the fold incorrectly.

**Property:**

For all queries Q across date range [D1, D2] in user's timezone, set of sessions returned is invariant under DST transitions occurring during [D1, D2].

**Implies:**
- Implies backend must convert date boundaries into UTC using user's timezone offset before filtering.
- Implies test harness needs clock-injection (freezegun) to simulate sessions landing on DST boundaries.
