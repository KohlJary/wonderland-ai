# Test Scenario 007: Feature 003 — Timezone handling (UTC assumption in v1)

**Feature:** Inspect historical session data across weeks and all-time
**Severity:** MEDIUM
**Concern:** Per the contract, v1 uses UTC-only for midnight boundaries (no local-timezone support). Sessions are grouped by date in UTC. If the client is in a different timezone, the daily aggregation may be off by a day.

## Scenario

Session completes at 2025-01-15 23:30 UTC. Client is in UTC+9 (Japan). On the client's local date (2025-01-16), the user navigates to the history screen and expects to see the session grouped under "today" (2025-01-16 local), but the backend groups it under "2025-01-15" (UTC).

## Assertion

Backend returns the session grouped under "2025-01-15" (UTC date of completion). Frontend receives this and displays it under "2025-01-15" in the history view, which is off from the user's local date perception. This is documented as a known limitation v1 (see ADR/Contract Note).

## Failure Mode

If timezone handling is not clear, the backend may incorrectly group sessions or the frontend may misinterpret the grouping, leading to sessions appearing under the wrong day.

## Test Implementation

See `tests/test_feature_003_history.py::test_timezone_utc_assumption`.
