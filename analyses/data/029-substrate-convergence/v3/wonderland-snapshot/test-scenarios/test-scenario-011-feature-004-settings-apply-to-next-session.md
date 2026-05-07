# Test Scenario 011: Feature 004 — Settings apply to *next* session, not current

**Feature:** Customize session and break lengths to fit personal rhythm
**Severity:** HIGH
**Concern:** Session lengths are captured at creation time from the Settings snapshot. Changing settings mid-session does NOT affect the running session's lengths. The new lengths apply only to the next session started after the change.

## Scenario

User starts a 25-minute session. After 5 minutes, user navigates to settings and changes focus_session_length_minutes from 25 to 20. User returns to the timer, which continues counting down 25 minutes (original length). After this session completes, user starts a new session, which uses the new 20-minute length.

## Assertion

Running session: countdown = 25 minutes (unchanged). SessionRecord for this session: session_duration_ms reflects 25 minutes. Next session started: countdown = 20 minutes (from updated Settings). SessionRecord for next session: session_duration_ms reflects 20 minutes.

## Failure Mode

Settings change retroactively applies to the running session (countdown suddenly jumps to 20 minutes). Or: new session still uses old settings because the change wasn't persisted correctly.

## Test Implementation

See `tests/test_feature_004_settings.py::test_settings_apply_to_next_session`.
