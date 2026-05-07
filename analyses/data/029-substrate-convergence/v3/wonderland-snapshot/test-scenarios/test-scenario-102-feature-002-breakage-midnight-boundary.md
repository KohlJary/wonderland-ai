# Test Scenario 102: Feature 002 — Breakage: Midnight Boundary

**Feature:** Review today's session activity at a glance
**Severity:** breakage
**Concern:** The 'today' count endpoint filters sessions completed between today-start (00:00) and today-end (23:59:59 local time). Frontend and backend disagree on the date boundary. Either: (1) Frontend doesn't detect midnight and keeps showing yesterday's count. (2) Backend's 'today' filter uses UTC midnight while frontend uses local midnight, so sessions near the boundary are misattributed. (3) The endpoint returns the same cached value without respecting the date reset. This is breakage because Maya will see wrong data and lose trust in the metrics.

## Scenario

Maya has completed 4 sessions today (by 11:55 PM). The frontend cached count=4. The app is still running or is reopened right after midnight (00:05 AM).

The system clock crosses midnight. The frontend detects the date change (local midnight, not UTC) or the user navigates back to the 'Today' view after midnight.

## Expected

The 'Today' count resets to 0 (no sessions completed yet in the new day). The session list is empty until Maya starts a new session and completes it.

## Failure Mode

Frontend caches yesterday's count and doesn't detect the boundary, so Maya sees count=4 at 12:05 AM (wrong). Or: backend returns sessions from both days in the 'today' count. Or: the cached response is served without respecting the date reset. Result: Maya sees corrupted metrics.

## Property

For all times T1 and T2 where T1 is before local midnight and T2 is after local midnight on the same calendar day, the set of sessions returned by GET /api/session-counts/today at T1 is disjoint from (does not overlap with) the set returned at T2.

## Test Implementation

See `tests/test_feature_002_midnight_boundary.py` for runnable tests.

## Implies

- Requires frontend/backend date-handling alignment—Tweedles own this, but it's a cross-domain seam.
- May imply architecture question about client-side caching vs. fresh fetches—flag for Cat if the pattern is systemic.
