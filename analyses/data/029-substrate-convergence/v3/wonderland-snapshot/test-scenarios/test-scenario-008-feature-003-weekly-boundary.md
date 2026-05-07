# Test Scenario 008: Feature 003 — Weekly boundary (7 days back from today)

**Feature:** Inspect historical session data across weeks and all-time
**Severity:** MEDIUM
**Concern:** GET /api/session-history/weekly returns sessions from [today - 7 days, today]. If the boundary is off (e.g., today - 6 days instead), a session from 8 days ago might be included or excluded incorrectly.

## Scenario

Today is 2025-01-15. Sessions were completed on 2025-01-08, 2025-01-09, ..., 2025-01-15. Call /api/session-history/weekly.

## Assertion

Response includes sessions from 2025-01-08 through 2025-01-15 (inclusive). Sessions from 2025-01-07 or earlier are excluded. The date range is exactly 7 days back (inclusive) plus today.

## Failure Mode

Off-by-one boundary error: includes 2025-01-07 (8 days back) or excludes 2025-01-08 (7 days back), resulting in missing or extra data in the weekly view.

## Test Implementation

See `tests/test_feature_003_history.py::test_weekly_boundary`.
