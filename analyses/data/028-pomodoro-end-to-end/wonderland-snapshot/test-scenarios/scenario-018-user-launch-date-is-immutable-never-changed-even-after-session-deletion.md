## Scenario 018: User launch date is immutable, never changed even after session deletion

**Severity:** breakage

**Setup:**

Marcus first session Jan 15, 2024 10:15 AM UTC. launch_date set. Later, all sessions deleted.

**Trigger:**

Query /user after deletion.

**Expected:**

launch_date = Jan 15, 2024 10:15 AM UTC (unchanged).

**Concern:**

If recalculated, could change or reset. Breaks immutability contract.

**Property:**

For all users, if launch_date set, it is never modified, even if all sessions deleted.
