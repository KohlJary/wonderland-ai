## Scenario 001: Historical data query edge cases — date validation, pagination, large result sets, timezone boundaries

**Severity:** silent-wrongness

**Setup:**

Priya has 3 weeks of history. She queries across various date ranges: reversed boundaries, future dates, large year-spanning queries. She also tests pagination with limit and offset.

**Trigger:**

GET /sessions/range with invalid dates, reversed date boundaries, empty future ranges, malformed date formats, and pagination parameters (limit, offset/page)

**Expected:**

Valid range returns sessions within bounds, ordered newest-first. Reversed dates return 400. Empty ranges return 200 with empty array. Pagination respects limits (capped at 500) and offsets correctly. All responses include sessions array (never null).

**Concern:**

Date filtering doesn't respect user timezone (11:59 PM session appears on wrong day). Pagination off-by-one or ignored entirely. Large result sets (365 days) time out or return partial data. Limit parameter ignored; all 500+ results returned. Empty result set returns null instead of [].

**Property:**

For all date ranges [start, end]: GET /sessions/range returns completed sessions S where S.created_at ∈ [start, end]. Sessions ordered start_time DESC. If start > end, return 400. If empty, return 200 with sessions=[]. Limit capped at 500. Offset skips correctly.

**Implies:**
- Implies timezone-aware DATE filtering for date boundaries
- Implies pagination support with limit-cap and offset/page handling
- Implies result-set size limits and performance testing for large ranges
- Implies date format validation (ISO8601 only)
