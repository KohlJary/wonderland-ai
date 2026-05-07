# Test Scenario 006: Feature 002 — Empty today count (no sessions yet)

**Feature:** Review today's session activity at a glance
**Severity:** MEDIUM
**Concern:** When no sessions have been completed today, the backend returns {count: 0, total_focus_minutes: 0}. Frontend must display this gracefully (not an error, not a loading state).

## Scenario

User opens the app on a new day with no sessions completed yet. Frontend fetches /api/session-counts/today.

## Assertion

Backend returns {count: 0, total_focus_minutes: 0}. Frontend renders an empty state UI (e.g., "No sessions yet") rather than showing a loading spinner or an error message.

## Failure Mode

Frontend treats count = 0 as a loading state (shows spinner indefinitely) or as an error (shows error message). User is confused.

## Test Implementation

See `tests/test_feature_002_today_count.py::test_empty_count`.
