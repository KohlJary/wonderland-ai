## Test Scenario 004: Review historical session data — query correctness

**Source:** feature-004-review-historical-session-data
**Persona:** Priya, 31, a program manager
**Severity:** high (historical accuracy is the core value of the feature)
**Concern:** Data accuracy across date ranges, pagination, and edge cases

---

## Happy Path

**Scenario: Priya queries this week's sessions**

1. Priya opens the history view
2. She sees "This Week: 12 sessions, 5 hours 15 minutes"
3. She taps to expand and sees a list of sessions, newest first
4. Each row shows start time, end time, and duration (e.g., "Mon 2:15 PM – 2:40 PM · 25m 30s")
5. She can scroll the list
6. **Observable outcome:** The count and total time match the sum of individual sessions

---

## Failure Modes

**Hatter's Breakdown:**

1. **Date range boundary violations** — user queries Jan 1–10, somehow gets Jan 20 sessions
   - **Why this matters:** Priya's data analysis depends on date correctness. Wrong range = misleading insight
   - **Severity:** high (silent wrongness)

2. **Pagination off-by-one** — user requests page 2 of results, gets duplicates from page 1
   - **Why this matters:** Large result sets need pagination; bad pagination loses or repeats data
   - **Severity:** high

3. **Deleted sessions in historical data** — Priya abandoned a session mid-work; it still appears in history
   - **Why this matters:** Historical count is inflated, defeats the purpose of abandonment feature
   - **Severity:** high

4. **Timezone boundary crossing** — session started in user's timezone at 11:50 PM, completed after midnight
   - **Why this matters:** "Today" boundary is ambiguous; session might count in wrong day
   - **Severity:** medium (depends on user's timezone awareness)

5. **Large result set timeout** — user queries a full year of data (1000+ sessions), backend times out
   - **Why this matters:** User can't access their own historical data
   - **Severity:** medium (only affects power users)

6. **Limit parameter bypass** — user requests &limit=10000 to fetch everything at once
   - **Why this matters:** Backend could OOM; needs to cap limit
   - **Severity:** medium

7. **Empty result set format** — query with no sessions returns null instead of empty list
   - **Why this matters:** Frontend crashes trying to iterate null
   - **Severity:** high (breakage)

8. **Race condition on concurrent queries** — two simultaneous range queries return different data
   - **Why this matters:** User sees inconsistent data (unlikely, but possible with bad isolation)
   - **Severity:** low (rare)

---

## Test Implementation

See `tests/test_session_004_historical_review.py`:

- **Happy path:** `TestHistoricalReviewHappyPath` — Priya fetches, pagina, views breakdown
- **Edge cases:** `TestHistoricalReviewEdgeCases` — boundary violations, pagination, timezone, etc.

**Red-green target:** All tests in `test_session_004_historical_review.py` should fail until M5 implements:
- GET /sessions/range?start_date=...&end_date=... endpoint
- Proper date range filtering
- Pagination (page, limit params)
- Ordering by start_time descending
- Exclusion of deleted sessions
