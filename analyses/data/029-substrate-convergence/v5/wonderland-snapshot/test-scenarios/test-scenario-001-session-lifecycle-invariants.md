## Test Scenario 001: Session Lifecycle Invariants

**Feature:** Start and complete a focus session (feature-001)
**Persona:** Technical — invariant validation, not persona-driven
**Stack span:** backend
**Severity:** critical

**Concern:**

The session lifecycle model (frontend-owned timer, POST /start → 202, PATCH /complete on expiry) depends on several non-negotiable invariants. If these break, the model fails:

- completed_at must be within a reasonable window (started_at to started_at + duration + jitter)
- A session can be completed at most once (idempotent or rejected on retry)
- Abandoned sessions (no /complete call) never persist
- Session IDs must exist before completion
- Duration must be positive and bounded (can't be 0, can't be 1 week)

These constraints enforce the contract's core claim: *the frontend owns the timer, the backend validates on completion*.

**Test Coverage:**

Implemented in `tests/test_feature_001_edge_cases.py`:

- `test_completed_at_must_be_within_expected_window` — validates the time window bounds
- `test_complete_same_session_twice_is_idempotent_or_rejected` — enforces idempotency
- `test_abandoned_sessions_never_persisted` — ensures no cleanup job is needed
- `test_session_id_must_exist_to_complete` — prevents fabricated session IDs
- `test_session_duration_must_be_positive` — enforces positive duration constraint
- `test_session_duration_has_reasonable_bounds` — enforces upper bounds

**Failure Mode Anticipated:**

A client could bypass the contract by:
- Submitting a completed_at far outside the expected range (time-travel attacks)
- Calling /complete multiple times (double-counting sessions)
- Inventing session IDs (session spoofing)
- Starting a session with invalid duration (0 or negative or multi-week)

If any of these succeed, the session record becomes untrustworthy and the user's history is corrupted.

**When This Test Passes:**

The backend enforces the contract's timing and ID constraints. The frontend timer ownership is validated.
