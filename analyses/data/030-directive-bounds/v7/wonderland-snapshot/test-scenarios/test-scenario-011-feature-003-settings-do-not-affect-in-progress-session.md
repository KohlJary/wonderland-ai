## Test Scenario: Settings changes must not affect in-progress sessions

**Severity:** medium

**Feature:** Feature-003 (Customize session and break durations)

**Setup:**

User starts a session with settings: focus_duration_seconds=1500, break_duration_seconds=300.

Frontend POST /sessions/start records the duration:
```json
{ "session_type": "focus", "focus_duration_seconds": 1500, "break_duration_seconds": 300 }
```

Backend returns session_id="abc-123" with time_remaining_seconds=1500.

**Trigger:**

While the session is running (15 minutes elapsed), user opens Settings and changes:
```json
{ "focus_duration_seconds": 2400, "break_duration_seconds": 300 }
```

Frontend PATCH /settings succeeds. But the user is still in the middle of a 25-minute session.

**Expected:**

The in-progress session continues with the original 1500-second duration. When the session completes at the 25-minute mark, the completed_at timestamp is recorded, and the session's focus_duration_seconds is 1500 (not retroactively changed to 2400).

The next session, when started, uses the new 2400-second setting.

**Concern:**

If settings changes propagate to in-progress sessions, the timer can jump or contract unexpectedly:
- User starts a 25-minute session, sees "25:00" on screen
- User changes settings to 50 minutes
- If the frontend re-renders the timer, it might show "50:00" mid-session
- User is confused about how much time is left

More insidiously, if the backend retroactively updates the session's focus_duration_seconds in the database, the historical record becomes inconsistent. Was the user working for 25 minutes or 50 minutes? The database record becomes ambiguous.

**Property:**

Settings changes are "prospective" — they affect only future sessions, not in-flight sessions.

When a session is started, the backend or frontend records the requested durations (focus_duration_seconds, break_duration_seconds) as immutable facts for that session. Changes to /settings after the session starts do not modify these values.

When a session completes, the recorded focus_duration_seconds is the value that was specified at session start, not the value in /settings at completion time.

**Mechanism:**

- Frontend: When starting a session, read current settings and pass them to POST /sessions/start. Store them in the session object. Do not re-read settings mid-session.
- Backend: Accept focus_duration_seconds and break_duration_seconds as parameters to /sessions/start and /sessions/complete. Store them as immutable facts with the session record. Do not look up the current user settings at completion time.

**Runnable Tests:**

- `tests/test_feature_003_edge_cases.py::test_feature_003_settings_do_not_affect_in_progress_session`
