## Scenario 011: Weekly stats use Monday-Sunday boundaries inclusive on both ends in UTC

**Severity:** silent-wrongness

**Setup:**

Elena queries /stats/week. A session completed Sunday 23:59:59 UTC should be included.

**Trigger:**

Backend computes with boundary: Monday 00:00 UTC <= completed_at <= Sunday 23:59:59 UTC.

**Expected:**

Session at Sunday 23:59 UTC included. Session at Monday 00:00 UTC included. Previous Sunday 23:59 NOT.

**Concern:**

If off-by-one, week totals wrong. Session in two weeks or missed.

**Property:**

For all sessions with completed_at in [Monday_00:00_UTC, Sunday_23:59:59_UTC], included in /stats/week.
