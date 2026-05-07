## Test Scenario 023: Changed settings apply to next session, not the current one

**Severity:** degradation

**Feature:** Feature 004: Customize session and break lengths to fit personal rhythm

**Setup:**

James starts a 25-minute session (using the default settings). 5 minutes into the session, he realizes he wants 50-minute sessions going forward. He opens Settings and changes focus_session_length from 25 to 50, then saves.

The current Session record (status=running, session_length_minutes=25) is still in progress. The Settings record in the DB is updated to focus_session_length=50.

**Trigger:**

James closes Settings and returns to the timer. The countdown continues from where it left off (20 minutes remaining in the original 25-minute session).

**Expected:**

The timer should NOT jump to a 50-minute countdown. The current session remains 25 minutes. When the current session completes, the next session (if started) will use the new 50-minute setting.

**Concern:**

If the implementation applies Settings changes retroactively to the current session, the user will see the countdown suddenly jump to 45 minutes (50 - 5 elapsed), or the session duration will appear to have changed mid-flight. This is confusing and breaks the user's trust in the timer.

Alternatively, if the backend doesn't snapshot Settings at session-creation time, and instead reads from the Settings table at session-completion time, the SessionRecord might be written with incorrect session_length_minutes.

**Property:**

For all sessions S created at time T0:
- S.session_length_minutes = Settings.focus_session_length at time T0 (snapshot, immutable for this session)
- Changes to Settings at time T1 (where T1 > T0) do NOT affect S.session_length_minutes

The current session uses its original settings; new sessions use new settings.

**Implies:**

This tests the Settings snapshot behavior (contract-note-005 specifies "Session snapshots settings at creation time"). The scenario validates that changing Settings doesn't retroactively affect in-progress sessions.

