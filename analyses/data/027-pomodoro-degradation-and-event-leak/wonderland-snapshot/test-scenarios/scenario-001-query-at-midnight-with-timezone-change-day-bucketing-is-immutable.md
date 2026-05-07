## Scenario 001: Query at midnight with timezone change—day-bucketing is immutable

**Severity:** silent-wrongness

**Setup:**

Focus session created at 11:55 PM PT (calendar day 15 PT = 04:55 UTC day 16). User device timezone changes from PT to ET.

**Trigger:**

User navigates to 'Today' view in ET timezone. App issues GET /sessions?fromDate=2024-01-16&toDate=2024-01-16.

**Expected:**

Session NOT included in day-16 ET query (created on day-15 PT in original timezone). Session IS included if queried for day-15. Day-bucketing is stable and doesn't re-bucket due to timezone change.

**Concern:**

App re-buckets sessions by current timezone instead of original timezone. Or caches bucketed date and loses it on TZ change. Silent wrongness: user sees session they just created disappear from 'Today' view, or sees sessions on wrong calendar day.

**Property:**

createdAt is UTC; day-bucketing computed in user's *local* timezone (current TZ); session's calendar day is immutable per original creation context. Timezone changes affect query results but don't re-bucket existing sessions.

**Implies:**
- Timestamps must be UTC (not local TZ) — flag for Tweedledum.
- Query semantics: date boundaries are in local TZ, converted to UTC for comparison — flag for contract review.
- Frontend cache invalidation when timezone changes — flag for Tweedledee.
