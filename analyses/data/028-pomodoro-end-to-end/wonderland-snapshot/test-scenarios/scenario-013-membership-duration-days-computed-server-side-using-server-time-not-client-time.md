## Scenario 013: Membership_duration_days computed server-side using server time, not client time

**Severity:** degradation

**Setup:**

Elena's device clock set 3 days in future. Queries /stats/all-time.

**Trigger:**

Backend computes membership_duration_days = floor((now_server - launch_date) / 86400).

**Expected:**

Returned value uses server time. Correct even if Elena's clock wrong.

**Concern:**

If computed client-side, wrong whenever user's clock incorrect.

**Property:**

For all users, membership_duration_days returned by /stats/all-time is computed server-side.
