# Test Scenario 002: Feature 001 — SessionRecord atomic write on completion

**Feature:** Run a focused work session with built-in break
**Severity:** CRITICAL
**Concern:** On session completion, the backend must atomically write a SessionRecord (append-only log entry) AND update Session.status to completed. If the write partially fails (e.g., SessionRecord written but Session.status not updated), the system enters an inconsistent state.

## Scenario

Session is running and reaches completion (countdown expires). Backend processes the completion event and writes to both Session and SessionRecord tables.

## Assertion

Both writes succeed (Session.status = completed AND SessionRecord appended) or both rollback. The session_duration_ms in SessionRecord matches the elapsed time from Session.started_at to completed_at, accounting for paused_duration_ms. If the transaction fails, the Session remains in running state and no SessionRecord is written.

## Failure Mode

Partial write (Session marked completed but SessionRecord not written) means the session is lost from history. Partial write (SessionRecord written but Session not marked completed) means the session appears both in-progress and completed, confusing the frontend.

## Test Implementation

See `tests/test_feature_001_state_machine.py::test_sessionrecord_atomic_write`.
