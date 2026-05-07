## Test Scenario 001: Session immutability and duration validation

**Feature:** Feature 001 (Start, run, complete focus session)
**Severity:** breakage

### Setup

A session record has been created with {start_time: T, session_duration_setting: 25 minutes, settings_snapshot captured at T}. The session is still running (end_time not yet set). User opens settings and changes session_duration to 15 minutes.

### Trigger

User saves the new 15-minute duration setting while the current session is still in progress.

### Expected

The in-progress session continues to use the 25-minute duration captured in its settings_snapshot. The setting change does NOT affect this session's expected end time. Only new sessions created after the setting change will use 15 minutes.

### Concern

Without explicit immutability enforcement on the settings_snapshot, the backend could silently use the new setting retroactively, making the session's recorded duration inconsistent with its actual runtime. This violates the contract: 'session records are immutable once created.'

### Property

For all session records S with settings_snapshot SS, the duration used to calculate end_time(S) must be SS.session_duration, never the user's current session_duration setting.

### Implies

- **Architectural**: Backend must validate that session end_time is calculated from settings_snapshot captured at start, not from current settings.
- **Coordination**: Frontend must capture settings_snapshot at session start and use that snapshot for the entire session duration, never re-reading settings mid-session.
