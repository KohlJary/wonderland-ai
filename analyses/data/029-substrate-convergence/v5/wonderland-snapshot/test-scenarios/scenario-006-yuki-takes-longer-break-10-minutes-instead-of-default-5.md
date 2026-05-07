## Scenario 006: Yuki takes longer break (10 minutes instead of default 5)

**Severity:** degradation

**Setup:**

Session completed. Yuki extends break UI to 10 minutes.

**Trigger:**

Frontend runs 600-second timer. POSTs /break-complete with completed_at = started_at + 1500 + 600.

**Expected:**

Backend accepts (no duration validation on break; frontend owns break UI). Session updated with completed_break_at.

**Concern:**

Backend might validate break_duration_seconds bounds, preventing longer breaks.

**Property:**

Backend does not validate break duration. Accepts any completed_at timestamp for /break-complete.

**Implies:**
- Test file: tests/test_breaks_and_transitions.py
