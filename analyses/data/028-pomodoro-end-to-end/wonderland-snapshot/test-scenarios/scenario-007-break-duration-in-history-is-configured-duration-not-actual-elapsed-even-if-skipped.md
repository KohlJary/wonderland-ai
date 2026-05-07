## Scenario 007: Break duration in history is configured duration, not actual elapsed (even if skipped)

**Severity:** silent-wrongness

**Setup:**

Priya completes session (5-min break configured). She immediately skips (actual elapsed <1s).

**Trigger:**

Query /sessions/history.

**Expected:**

break_duration_seconds = 300 (5 min * 60), NOT 0. Records *intended* duration.

**Concern:**

If records actual (0), history ambiguous: skip vs. 0-second break? Silent wrongness.

**Property:**

For all sessions in history, break_duration_seconds == configured_duration_at_creation.
