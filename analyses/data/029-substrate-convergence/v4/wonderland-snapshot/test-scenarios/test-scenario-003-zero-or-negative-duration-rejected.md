## Test Scenario 003: Zero or negative duration rejected

**Feature:** Feature 001 (Start, run, complete focus session)
**Severity:** degradation

### Setup

A client (buggy or adversarial) sends a session completion request with start_time=09:00:00, end_time=08:59:00 (negative duration, or end before start).

### Trigger

Backend receives POST /sessions with duration_seconds=-60 or duration_seconds=0.

### Expected

Backend rejects the request with 400 Bad Request. Session is not recorded. Client receives a clear error message.

### Concern

Without validation, negative or zero durations could be persisted, corrupting history. Queries for 'total focus time' would return impossible values (negative hours or zero). This is a data integrity issue and violates the implicit contract that all sessions have positive duration.

### Property

For all session records S, duration_seconds > 0.

### Implies

- **Backend validation**: Reject any session POST where duration_seconds <= 0.
