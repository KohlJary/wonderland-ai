## Scenario 004: Completion timestamp set exactly at transition moment for precise duration calculations

**Severity:** silent-wrongness

**Setup:**

James's session 4 seconds from completion. He taps Stop.

**Trigger:**

Backend transitions to completed, sets completed_at to current server timestamp.

**Expected:**

completed_at is between start_time and current_time, precise to milliseconds. Downstream calculations correct.

**Concern:**

If set retroactively or with timezone bugs, session duration wrong by hours. Silent wrongness: stats look reasonable but subtly wrong.

**Property:**

For all completed sessions, (completed_at - start_time) ≈ intended_duration (within 1% tolerance).
