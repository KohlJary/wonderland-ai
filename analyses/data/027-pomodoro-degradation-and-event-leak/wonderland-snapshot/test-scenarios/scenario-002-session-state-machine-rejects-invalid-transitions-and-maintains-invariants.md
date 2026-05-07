## Scenario 002: Session state machine rejects invalid transitions and maintains invariants

**Severity:** breakage

**Setup:**

Session with completionStatus='completed' (terminal state). Valid transitions: pending→{completed, extended}. No backward, no branching.

**Trigger:**

PATCH /sessions/{id} attempts invalid transition: completed→pending (backward), or completed→extended (already terminal).

**Expected:**

PATCH rejected with 400 Bad Request. Response includes reason. Session unchanged. No partial updates. Invariant maintained: completionStatus='completed'|'extended' ⟹ actualDuration≠null.

**Concern:**

Backend doesn't validate state transitions. Accepts invalid enum values and stores them. Corrupts invariant: status='completed' but actualDuration=null, breaking downstream logic. Partial updates leave record inconsistent.

**Property:**

(1) completionStatus transitions one-way only (pending→completed|extended, never backward). (2) Invariant: status='completed|extended' ⟹ actualDuration≠null. (3) Partial updates not allowed; PATCH succeeds entirely or fails entirely.

**Implies:**
- Backend validation: state transition function validates proposed transition before applying — flag for Tweedledum.
- Error response includes reason, not just HTTP 400 — flag for contract.
- Atomicity: database constraints/transactional logic prevent partial updates — flag for Tweedledum.
