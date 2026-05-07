## Scenario 007: Maya crosses midnight and the 'Today' count still shows yesterday's sessions

**Severity:** breakage

**Setup:**

Maya has completed 4 sessions today (by 11:55 PM). The frontend cached count=4. The app is still running or is reopened right after midnight (00:05 AM).

**Trigger:**

The system clock crosses midnight. The frontend detects the date change (local midnight, not UTC) or the user navigates back to the 'Today' view after midnight.

**Expected:**

The 'Today' count resets to 0 (no sessions completed yet in the new day). The session list is empty until Maya starts a new session and completes it.

**Concern:**

Frontend and backend disagree on the date boundary. Either: (1) Frontend doesn't detect midnight and keeps showing yesterday's count. (2) Backend's 'today' filter uses UTC midnight while frontend uses local midnight, so sessions near the boundary are misattributed. (3) The endpoint returns the same cached value without respecting the date reset. This is breakage because Maya will see wrong data and lose trust in the metrics.

**Property:**

For all times T1 and T2 where T1 is before local midnight and T2 is after local midnight on the same calendar day, the set of sessions returned by GET /api/session-counts/today at T1 is disjoint from (does not overlap with) the set returned at T2.

**Implies:**
- Requires frontend/backend date-handling alignment—Tweedles own this, but it's a cross-domain seam.
- May imply architecture question about client-side caching vs. fresh fetches—flag for Cat if the pattern is systemic.
