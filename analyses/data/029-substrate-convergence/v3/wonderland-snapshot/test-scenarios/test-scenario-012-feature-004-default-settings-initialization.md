# Test Scenario 012: Feature 004 — Default settings initialization on first GET

**Feature:** Customize session and break lengths to fit personal rhythm
**Severity:** MEDIUM
**Concern:** On first app startup, GET /api/settings should return default settings (focus_session_length_minutes = 25, break_length_minutes = 5). If the Settings table is empty, the backend creates and returns a default row.

## Scenario

First app startup. Settings table is empty (no user has configured anything yet). Frontend calls GET /api/settings.

## Assertion

Backend creates a default Settings row with focus_session_length_minutes = 25, break_length_minutes = 5, and returns it. Subsequent GET /api/settings calls return the same row (no re-creation). User sees default values in the settings screen.

## Failure Mode

GET returns an error (e.g., "Settings not found") instead of initializing defaults. Or: defaults are created on-write only (POST), leaving GET with no data to return on first startup.

## Test Implementation

See `tests/test_feature_004_settings.py::test_default_settings_initialization`.
