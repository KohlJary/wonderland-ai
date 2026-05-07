# Test Scenario 005: Feature 002 — Today's session count at midnight boundary

**Feature:** Review today's session activity at a glance
**Severity:** HIGH
**Concern:** The endpoint GET /api/session-counts/today filters sessions completed between today-start (00:00) and today-end (23:59:59 local time). If a session completes at 23:59 and another at 00:01 (next day), the count must split correctly across days. If the client's date wraps at midnight, the cached count must reset.

## Scenario

User completes a session at 23:55 (today). Frontend has cached count = 3. At 00:05 (tomorrow), the frontend detects date change (local midnight crossed). The app refetches /api/session-counts/today.

## Assertion

First /api/session-counts/today returns count including the 23:55 session. Second /api/session-counts/today (after midnight) returns count = 0 (no sessions completed "today" yet). The frontend correctly clears and resets its cache on midnight boundary.

## Failure Mode

Midnight boundary not detected: frontend keeps showing yesterday's count. Or: count includes sessions from both days, or excludes sessions completed right before midnight.

## Test Implementation

See `tests/test_feature_002_today_count.py::test_midnight_boundary`.
