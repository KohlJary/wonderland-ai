# Test Scenario 001: Feature 001 — Invalid state transition (Session state machine violation)

**Feature:** Run a focused work session with built-in break
**Severity:** CRITICAL
**Concern:** Session state machine must enforce valid transitions (new→running→paused|completed). Invalid transitions like paused→paused or completed→running must be rejected at the database level or application layer before write.

## Scenario

Backend receives a state transition request that violates the state machine (e.g., attempt to transition a completed session back to running, or attempt to pause a session that is already paused).

## Assertion

The backend rejects the invalid transition with an HTTP 400 (Bad Request) or 409 (Conflict) response, naming the invalid transition. The Session record in the database is NOT updated. The invariant "session has exactly one valid state at any time" is preserved.

## Failure Mode

If invalid transitions are allowed, the session can enter an undefined state. The frontend's UI state machine becomes misaligned with the backend's state, leading to user confusion or data loss.

## Test Implementation

See `tests/test_feature_001_state_machine.py::test_invalid_state_transition`.
