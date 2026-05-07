## Scenario 012: Empty history: New user views today's count and stats

**Severity:** curiosity

**Setup:**

New user, zero sessions in database.

**Trigger:**

Frontend GETs /sessions/today and /sessions/stats?period=week.

**Expected:**

Both return empty results gracefully. No null or 500 errors.

**Concern:**

Backend might crash on empty result or return 404.

**Property:**

All history/stats queries return valid responses, never null.

**Implies:**
- Test file: tests/test_session_history.py
