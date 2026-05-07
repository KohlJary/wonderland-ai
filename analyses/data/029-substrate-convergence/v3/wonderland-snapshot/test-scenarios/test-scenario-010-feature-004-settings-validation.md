# Test Scenario 010: Feature 004 — Settings validation constraints

**Feature:** Customize session and break lengths to fit personal rhythm
**Severity:** HIGH
**Concern:** Per the contract, settings validation: focus_session_length_minutes must be in [5, 60], break_length_minutes must be in [5, 30]. Backend enforces these constraints on write. Invalid values are rejected.

## Scenario

User submits a settings update with focus_session_length_minutes = 120 (exceeds max 60) or break_length_minutes = 2 (below min 5).

## Assertion

Backend rejects the request with HTTP 400 (Bad Request), explaining the constraint violation. Settings table is NOT updated. User receives an error message prompting them to enter a value within the valid range.

## Failure Mode

Invalid settings are accepted and persisted, causing sessions to be created with out-of-spec durations. Or: the constraint is enforced on the client only (frontend trusts backend), and a malicious or offline client can bypass it.

## Test Implementation

See `tests/test_feature_004_settings.py::test_settings_validation`.
