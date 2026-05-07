## Scenario 019: Launch date is exact timestamp of first session, not normalized to midnight

**Severity:** degradation

**Setup:**

Marcus first session 10:15:33 AM UTC Jan 15, 2024.

**Trigger:**

GET /user.

**Expected:**

launch_date = '2024-01-15T10:15:33Z' (exact), NOT '2024-01-15T00:00:00Z'.

**Concern:**

If normalized, days_tracked calculation off by up to 1 day.

**Property:**

For all users, launch_date equals exact timestamp of first session, precise to second.
