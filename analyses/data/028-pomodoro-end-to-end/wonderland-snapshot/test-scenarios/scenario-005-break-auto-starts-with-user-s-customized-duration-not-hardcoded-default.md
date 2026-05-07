## Scenario 005: Break auto-starts with user's customized duration, not hardcoded default

**Severity:** degradation

**Setup:**

Priya customized break to 10 min (default 5). She completes session.

**Trigger:**

Session completes, backend initializes break with duration from user.settings.

**Expected:**

/break/current returns {duration_minutes: 10}. User sees 10:00 countdown.

**Concern:**

If hardcoded, Priya's settings silently ignored. System works but not customized.

**Property:**

For all breaks created after session completion, break.duration_minutes == user.settings.break_duration_minutes.

**Implies:**
- Implies coordination with Feature 005: settings must be fetched fresh on completion.
