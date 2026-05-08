## Scenario: User views daily review on a day with no sessions

**Severity:** degradation

**Setup:**

Today is Sunday. David didn't start any focus sessions today (he's resting). He opens the daily review screen.

**Trigger:**

GET /api/daily-review?date=2024-01-07

**Expected:**

The daily review returns:
```json
{
  "date": "2024-01-07",
  "completed_focus_count": 0,
  "completed_break_count": 0,
  "skipped_break_count": 0,
  "total_focus_time_ms": 0
}
```

The UI displays "0 sessions, 0 breaks, 0 minutes" cleanly without crashing.

**Concern:**

If the query is implemented as a SUM and COUNT with an implicit GROUP BY, and there are no rows matching the date, the query might return NULL instead of 0. A COUNT(*) with no matching rows returns 0 (correct), but a SUM with no rows returns NULL (incorrect). The frontend might try to render NULL and crash, or display "undefined".

Alternatively, if the backend doesn't handle the empty case, it might 404 instead of returning 0s.

**Property:**

For all dates D with no sessions:
- daily-review(D) must return a well-formed response with all counts=0, sum=0
- No NULL values; no 404

**Implies:**

- Implies backend query: handle COUNT/SUM aggregation for zero-row case
- Implies test: cover the zero-row case explicitly
