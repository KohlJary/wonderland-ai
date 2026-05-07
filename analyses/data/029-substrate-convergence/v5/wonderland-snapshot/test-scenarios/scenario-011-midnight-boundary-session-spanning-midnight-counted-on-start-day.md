## Scenario 011: Midnight boundary: Session spanning midnight counted on start day

**Severity:** silent-wrongness

**Setup:**

User completed session at 11:55 PM UTC on May 1. Break finished 12:05 AM UTC on May 2.

**Trigger:**

Frontend queries /sessions?from_date=2024-05-01&to_date=2024-05-02.

**Expected:**

Session counted in May 1's history (started_at is grouping key). Session appears in GET /sessions/today (May 1).

**Concern:**

Contract doesn't explicitly state that started_at is the only grouping field.

**Property:**

Sessions grouped by started_at only. Session started day X belongs to day X.

**Implies:**
- Test file: tests/test_session_history.py
