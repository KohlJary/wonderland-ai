## Scenario: Break session is logged with correct status (completed vs. skipped)

**Severity:** silent-wrongness

**Setup:**

David completes a focus session. A break session is auto-started. David can either:
1. Complete it (wait 5 minutes) → should log as "break_completed"
2. Skip it (press "skip break") → should log as "break_skipped"

The contract note says daily review counts "completed breaks" and "skipped breaks" separately so David can see adherence.

**Trigger:**

David completes 2 focus sessions, gets 2 break sessions:
- Break 1: he waits the full 5 minutes. Then completes it.
- Break 2: he skips after 30 seconds.

Then David views daily review.

**Expected:**

Daily review shows:
- 2 completed focus sessions
- 1 completed break
- 1 skipped break

**Concern:**

If the event log doesn't distinguish break_completed from break_skipped, the daily review can't compute adherence. If the backend lumps them together, the count(breaks) will be right but count(completed_breaks) and count(skipped_breaks) will both be 0 or undefined. The UI will either display "N/A" or crash trying to access missing fields.

Also: the event log must actually log skipped breaks, not just silently discard them. If a user skips a break and no event is logged, the daily review will show 2 completed breaks (the ones logged) and 0 skipped breaks (never logged), even though David actually skipped one.

**Property:**

For all breaks B on day D:
- If B.status == 'completed': day_D.completed_breaks must include B
- If B.status == 'skipped': day_D.skipped_breaks must include B
- count(completed_breaks) + count(skipped_breaks) must equal total breaks initiated

**Implies:**

- Implies backend schema: event log must have a status field (or type field) that distinguishes break_completed from break_skipped
- Implies frontend contract: when user skips a break, a completion event with status='skipped' must be POSTed
- Implies contract note: spec must clarify what "skipped" means (timeout, user pressed skip, user navigated away?)
