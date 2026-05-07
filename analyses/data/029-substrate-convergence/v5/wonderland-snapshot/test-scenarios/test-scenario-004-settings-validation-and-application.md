## Test Scenario 004: Settings Validation and Application Invariants

**Feature:** Customize session and break durations (feature-004)
**Persona:** Technical — invariant validation, not persona-driven
**Stack span:** backend
**Severity:** high

**Concern:**

Settings customization depends on invariants that ensure the user's preferences are valid and applied correctly:

- Duration values must fall within bounds (60s to 7200s per story-005)
- Partial updates preserve unspecified fields (updating one duration doesn't zero the other)
- Settings changes apply only to the *next* session, not mid-session
- Each update includes a settings_updated_at timestamp (for frontend versioning)
- Empty or invalid PUT requests are rejected or handled gracefully
- Durations must be positive numbers, not strings or negative values

These constraints maintain the invariant: *settings are always valid, and changes are applied predictably*.

**Test Coverage:**

Implemented in `tests/test_feature_004_edge_cases.py`:

- `test_settings_duration_bounds_validation` — enforces the [60s, 7200s] range
- `test_settings_partial_update_preserves_unspecified_fields` — ensures no unintended zeroing
- `test_settings_change_applies_to_next_session_only` — validates timing of application
- `test_settings_timestamp_tracks_when_they_were_updated` — enforces versioning
- `test_settings_empty_put_preserves_all_values` — handles edge-case requests
- `test_settings_invalid_type_rejected` — validates type constraints
- `test_settings_negative_duration_rejected` — enforces positivity
- `test_settings_zero_duration_rejected` — enforces > 0 (not >= 0)

**Failure Mode Anticipated:**

Settings could become invalid if:
- A user accidentally sets a 1-second or 1-week duration (bounds bypass)
- A partial update zeros out the other duration (incomplete transaction)
- A settings change mid-session affects that session's duration (contract violation)
- The frontend can't track which settings version a session used (missing timestamp)
- An empty or malformed request corrupts settings (no validation)

If any of these occur, the user's custom rhythm is either enforced incorrectly or lost.

**When This Test Passes:**

Settings are always valid, updates are atomic and predictable, and the frontend can reliably version settings against sessions.
