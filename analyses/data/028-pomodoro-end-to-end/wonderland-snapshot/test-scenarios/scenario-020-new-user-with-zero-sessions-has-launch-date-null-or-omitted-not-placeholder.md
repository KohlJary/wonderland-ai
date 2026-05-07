## Scenario 020: New user with zero sessions has launch_date=null or omitted, not placeholder

**Severity:** degradation

**Setup:**

Fresh user, zero sessions. Queries /user.

**Trigger:**

Endpoint returns user object.

**Expected:**

launch_date is null, empty string, or omitted. NOT placeholder like '2024-01-01'.

**Concern:**

If placeholder, user's stats show wrong membership duration.

**Property:**

For all users with zero sessions, launch_date is null or omitted from /user.
