## Test Scenario: Historical Data Query Edge Cases

**Severity:** silent-wrongness, degradation

**Setup:**

Priya has 3 weeks of session history. She queries for specific date ranges to analyze her focus patterns. The system must return consistent, correct data across various query shapes (large ranges, empty ranges, date boundaries, pagination).

**Trigger:**

Priya makes successive queries:
1. GET /sessions/range?start_date=2024-01-01&end_date=2024-01-31 (full month)
2. GET /sessions/range?start_date=2024-01-15&end_date=2024-01-10 (reversed dates)
3. GET /sessions/range?start_date=2030-01-01&end_date=2030-01-31 (future, no sessions)
4. GET /sessions/range with invalid date formats
5. GET /sessions/range?start_date=today&end_date=today&page=1&limit=5 (pagination)

**Expected:**

1. Valid date range returns sessions within that range, ordered newest-first
2. Reversed date range returns 400 Bad Request (invalid input)
3. Future date range returns 200 OK with empty sessions array
4. Malformed dates (01-01-2024, 2024/01/01) return 400 Bad Request
5. Pagination params work correctly: limit caps at 500, offset/page boundaries are correct
6. All responses include sessions array (never null), summary with count

**Concern:**

Silent-wrongness failure modes:
- Large date range (365 days) times out or returns partial data
- Query returns sessions outside the requested range
- Pagination offset is off by one or ignored entirely
- Timezone boundaries cause sessions to appear on wrong date (user in JP timezone, session created 11:50 PM local, query for yesterday gets the session anyway)
- Limit parameter is ignored; client requests &limit=5 and gets 500 results
- Empty result set returns null instead of []

Degradation:
- Invalid date format crashes backend (500)
- Reversed date range causes confusing error or silent empty result
- Very large result set (1000 sessions) causes OOM or timeout

**Property:**

For all users U and date ranges [start_date, end_date]:
- GET /sessions/range returns all completed sessions S where S.created_at is between start_date and end_date (inclusive)
- If start_date > end_date, return 400 Bad Request
- If no sessions exist in range, return 200 OK with sessions=[]
- Sessions are ordered by start_time descending (newest first)
- Pagination: limit is capped at 500, offset skips correctly
- All timestamps in response are ISO8601 strings

**Implies:**

- Implies date validation in /sessions/range endpoint
- Implies pagination support with limit (capped) and offset/page params
- Implies timezone-aware date filtering (DATE(created_at AT TIME ZONE user_tz) = requested_date)
- Implies result-set size limits and performance testing for large ranges
