## Scenario: Historical query across DST boundary returns correct count despite timezone shift

**Severity:** silent-wrongness

**Setup:**

User is in America/Los_Angeles timezone. Sessions completed on the day DST ends (November 2024):
- One session at 10 AM PDT (before the shift)
- One session at 1 AM PST (after the local time falls back, but same UTC instant as 2 AM PDT)

Query: `GET /sessions/range?start_date=2024-11-02&end_date=2024-11-02` expecting both sessions in today's results.

**Trigger:**

Frontend sends a date-range query for Nov 2 (local date).

**Expected:**

The response includes both sessions. The DST boundary—where local 1:59:59 becomes 0:59:59 (the hour repeats)—is handled correctly by the server. No sessions are filtered out due to a misunderstanding of the timezone fold.

**Concern:**

Timezone handling in historical queries is fragile. Backend may store times in UTC (correct), but the date-boundary logic may use naive local-date calculation without accounting for the timezone offset, causing sessions near the boundary to be dropped or duplicated. The UTC hours are correct, but the local-date interpretation gets them wrong.

**Property:**

For all queries Q across a date range [D1, D2] in the user's timezone, the set of sessions returned is invariant under DST transitions that occur within the user's timezone during [D1, D2].

**Implies:**

- Implies backend date-boundary logic must convert the user's configured timezone into UTC offsets before filtering. A date like "2024-11-02" in Los_Angeles is actually a range [2024-11-02 00:00:00 -07:00 ... 2024-11-02 23:59:59 -08:00] (different UTC offsets due to the shift).
- Implies test harness needs either: (a) real clock injection via freezegun or similar, or (b) manual UTC time injection to simulate sessions landing on the DST boundary.
