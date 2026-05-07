## Test Scenario 024: Default settings are created idempotently on first GET

**Severity:** degradation

**Feature:** Feature 004: Customize session and break lengths to fit personal rhythm

**Setup:**

A new user installs the app for the first time. No Settings record has been created in the DB yet. The frontend loads and immediately calls GET /api/settings (to populate the UI).

**Trigger:**

The GET /api/settings request hits the backend. The Settings table is empty.

**Expected:**

The backend returns HTTP 200 with:
```json
{
  "focus_session_length_minutes": 25,
  "break_length_minutes": 5
}
```

Additionally, a Settings record is created in the DB (if none existed) with these default values. Subsequent calls to GET /api/settings return the same values (either the created defaults or any user-customized values).

**Concern:**

If the backend returns a 404 when Settings don't exist, the frontend will show an error or blank state. The user won't be able to use the app until they explicitly set preferences (a bad UX).

If the backend doesn't create defaults idempotently, multiple concurrent requests to GET /api/settings might create duplicate Settings records, or a race condition might occur.

If the backend doesn't guarantee that Settings always exist, other endpoints that depend on Settings (e.g., POST /api/session/start) might crash or return errors.

**Property:**

For all users U and times T >= (U.install_time):
  GET /api/settings(U) returns HTTP 200 with valid default or customized Settings
  The response is idempotent: repeated calls return the same values
  Settings record exists in DB: count(Settings where user_id=U) >= 1

**Implies:**

This tests the idempotent default creation in the Settings endpoint (contract-note-005). The scenario validates that new users can immediately use the app without manual configuration.

