# Test Scenario 009: Feature 003 — Empty history (no sessions recorded)

**Feature:** Inspect historical session data across weeks and all-time
**Severity:** LOW
**Concern:** When no sessions have been recorded, both weekly and all-time endpoints return an empty array. Frontend must display this as an empty state, not an error.

## Scenario

User opens the app with no sessions completed. Frontend fetches /api/session-history/weekly and /api/session-history/all-time.

## Assertion

Both endpoints return [] (empty array). Frontend displays an empty state UI (e.g., "No sessions recorded yet") rather than a loading spinner or error.

## Failure Mode

Frontend treats empty response as a loading state or error, confusing the user.

## Test Implementation

See `tests/test_feature_003_history.py::test_empty_history`.
