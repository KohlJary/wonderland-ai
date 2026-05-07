## Test Scenario 002: Break State Invariants

**Feature:** Take a break and return to focus (feature-002)
**Persona:** Technical — invariant validation, not persona-driven
**Stack span:** backend
**Severity:** critical

**Concern:**

The break model (break as nullable completed_break_at property on session, frontend owns break timer, POST /break-complete on expiry) depends on several invariants:

- break-complete can only be called on a session that has already completed (completed_at is not null)
- completed_break_at starts null; only populated by /break-complete
- break-complete timestamp must be after session completion (no time-travel)
- /break-complete should be idempotent on retry
- /break-complete must return the full session record so the frontend can validate the write

These constraints maintain the invariant: *a break is always paired with a completed session, and break state is immutable once set*.

**Test Coverage:**

Implemented in `tests/test_feature_002_edge_cases.py`:

- `test_break_complete_requires_session_to_be_completed_first` — enforces the pairing invariant
- `test_completed_break_at_starts_null` — ensures nullable behavior
- `test_break_complete_timestamp_must_be_after_session_completion` — prevents time-travel
- `test_break_complete_idempotency` — enforces retry safety
- `test_break_complete_returns_full_session_record` — ensures frontend validation

**Failure Mode Anticipated:**

A client could violate break state by:
- Calling /break-complete on an in-progress session (session-break pairing broken)
- Submitting a break-complete timestamp before the session ended (time-travel)
- Calling /break-complete twice with different timestamps (state mutation)
- Receiving only {status: ok} without the record (can't validate the write)

If any of these succeed, the break state becomes untrustworthy.

**When This Test Passes:**

The backend enforces the break-session pairing and the immutability of completed_break_at once set.
