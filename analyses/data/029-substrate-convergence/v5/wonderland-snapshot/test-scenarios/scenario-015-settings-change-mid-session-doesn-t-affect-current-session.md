## Scenario 015: Settings change mid-session doesn't affect current session

**Severity:** degradation

**Setup:**

User started session with 1500s. Session running (frontend owns timer).

**Trigger:**

User opens settings, changes to 1800s.

**Expected:**

Current session records with 1500s. Next session uses 1800s.

**Concern:**

Frontend owns timer; backend is passive.

**Property:**

In-flight sessions not affected by settings changes.

**Implies:**
- Test file: tests/test_settings.py
