## Scenario 007: Yuki skips break, starts next session immediately

**Severity:** degradation

**Setup:**

Session completed. Break notification appears. Yuki taps 'Start Next Session'.

**Trigger:**

Frontend skips /break-complete, goes directly to POST /sessions/start for session 2.

**Expected:**

Session 2 starts successfully. Previous session's completed_break_at remains NULL.

**Concern:**

Backend might enforce break-complete before allowing next session.

**Property:**

Backend does not enforce break-complete. Next /sessions/start succeeds regardless.

**Implies:**
- Test file: tests/test_breaks_and_transitions.py
