## Scenario: Session state machine rejects invalid transitions

**Severity:** breakage

**Setup:**
A session exists with completionStatus='pending'. The session's state machine defines valid transitions:
- pending → completed (when timer completes or user manually marks complete)
- pending → extended (when user taps "pause" or "stop early")
- completed → (no transitions allowed; terminal state)
- extended → (no transitions allowed; terminal state)

**Trigger:**
Backend receives a PATCH /sessions/{id} attempting to transition to an invalid state. Examples:
- completionStatus='completed' → 'pending' (backward, not allowed)
- completionStatus='completed' → 'extended' (already terminal, can't branch)
- completionStatus='pending' → 'unknown' (invalid enum value)

**Expected:**
The PATCH request is rejected with HTTP 400 Bad Request. The response includes a reason field explaining the violation (e.g., "completionStatus cannot transition from completed to pending"). The session record is unchanged. No partial updates occur.

**Concern:**
The backend might not validate the state transition at all. It might accept a PATCH to set completionStatus='pending' on a session that's already 'completed', corrupting the session history. Or it might accept invalid enum values and store them, causing downstream errors in queries or notifications. Or it might update the session partially (actualDuration gets set but completionStatus update fails), leaving the record in an inconsistent state.

The silent wrongness: the session's completionStatus is now inconsistent with actualDuration (e.g., status='completed' but actualDuration=null, or status='pending' but actualDuration=25). Downstream logic that assumes completionStatus='completed' ⟹ actualDuration≠null will break.

**Property:**
For all session state transitions: validate that the proposed transition is in the set of valid transitions. If not, reject with 400 and reason, and leave the record unchanged. State machine must be enforced as an invariant, not a suggestion.

More broadly: For all sessions, the following must always hold (invariant):
- completionStatus='pending' ⟹ actualDuration is null
- completionStatus='completed' or 'extended' ⟹ actualDuration is not null
- actualDuration is not null ⟹ completionStatus is 'completed' or 'extended'
- completionStatus can only move forward in the machine, never backward or sideways

**Implies:**
- Implies validation on PATCH: backend must check the proposed transition before applying it. Flag for Tweedledum.
- Implies error response shape: error must include reason, not just HTTP 400. Clients need to display the error to users. Flag for contract review.
- Implies atomicity: the PATCH must succeed entirely or fail entirely. No partial updates. Database constraints (foreign keys, triggers) can enforce this. Flag for Tweedledum.
- Implies testing: the state machine itself is testable separately (unit test of transition function) before it's deployed in the API. Flag for implementation approach.
