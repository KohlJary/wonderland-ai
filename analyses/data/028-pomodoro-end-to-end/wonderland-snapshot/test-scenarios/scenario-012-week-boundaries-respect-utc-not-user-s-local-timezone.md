## Scenario 012: Week boundaries respect UTC, not user's local timezone

**Severity:** silent-wrongness

**Setup:**

Elena (UTC-8) Sunday evening local (1 AM UTC Monday) completes session. Queries /stats/week.

**Trigger:**

Backend computes week boundary using UTC.

**Expected:**

Session counted in next week (UTC Monday is next start), not this week (her local view).

**Concern:**

If uses local timezone, Elena's data misaligned with UTC.

**Property:**

For all users, /stats/week uses UTC week boundaries (Mon–Sun UTC), not local timezone.
