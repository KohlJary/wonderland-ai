## Scenario 016: Active session duration not retroactively changed when settings updated mid-session

**Severity:** degradation

**Setup:**

Dev starts 25-min session (default). 5 min in, changes to 50 min via Settings.

**Trigger:**

PATCH /settings processes.

**Expected:**

Active session still 25 min (not retroactively extended). Only next session uses 50.

**Concern:**

If applies retroactively, timer jumps mid-session. User trust broken.

**Property:**

For all active sessions, if PATCH /settings called, active session.duration_minutes does not change.
