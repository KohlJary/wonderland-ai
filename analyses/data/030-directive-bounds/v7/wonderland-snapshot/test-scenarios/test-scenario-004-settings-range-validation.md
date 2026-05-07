## Test Scenario: User sets focus_duration to 0 minutes or 100 minutes

**Severity:** silent-wrongness

**Feature:** Feature-003 (Customize session and break durations)

**Setup:**

User opens settings form. The UI has sliders or input fields for `focus_duration_seconds` and `break_duration_seconds`. Riley, the persona from the story, is willing to experiment with values outside the documented range (e.g., tries 0 minutes or 500 minutes out of curiosity or misunderstanding).

**Trigger:**

Riley enters an out-of-range value (0, -1, 500 minutes) and submits the PATCH /settings request. Backend receives the request.

**Expected:**

Backend validates the incoming durations and rejects the request with a 422 status (validation error). Valid ranges: focus_duration between 5–60 minutes, break_duration between 1–30 minutes. Settings are not updated. Frontend receives 422 error, shows user a message like "Focus duration must be between 5 and 60 minutes."

**Concern:**

Backend doesn't validate and accepts the invalid duration. Invalid values are stored in the database. Next time the user starts a session, the app tries to start a 0-minute session (completes instantly, nonsensical) or a 500-minute session (user is locked in for over 8 hours, can't escape). Silent wrongness: the setting was saved, the app appears to work, but the behavior is broken and the corruption is stored persistently. On app restart, the invalid setting is still there, propagating the damage.

**Property:**

For all PATCH /settings requests, if `focus_duration_seconds` is not in the range [300, 3600] (5–60 minutes) or `break_duration_seconds` is not in the range [60, 1800] (1–30 minutes), the request must be rejected with 422 status and the stored settings must not be updated.

**Implies:**

- Backend must validate all incoming durations, not trusting the frontend's UI constraints. Frontend validation is UX; backend validation is defense.

**Runnable Tests:**

- `tests/test_settings_failures.py::TestSettingsOutOfRangeBoundaries::test_focus_duration_below_minimum_is_rejected`
- `tests/test_settings_failures.py::TestSettingsOutOfRangeBoundaries::test_focus_duration_above_maximum_is_rejected`
- `tests/test_settings_failures.py::TestSettingsOutOfRangeBoundaries::test_focus_duration_zero_is_rejected`
- `tests/test_settings_failures.py::TestSettingsPersistenceAcrossRestarts::test_get_settings_returns_defaults_for_new_user`
