## Scenario 008: Session history returned in strict descending order by completed_at, consistent across queries

**Severity:** degradation

**Setup:**

James completes 5 sessions over 30 min. Queries /sessions/history multiple times.

**Trigger:**

Endpoint returns array ordered DESC. Query repeated.

**Expected:**

Results ordered identically every time. For all i, history[i].completed_at >= history[i+1].completed_at.

**Concern:**

If ordering unstable, UI flickers or user sees inconsistent state.

**Property:**

For all queries with same params, order is consistent across calls within 1s.
