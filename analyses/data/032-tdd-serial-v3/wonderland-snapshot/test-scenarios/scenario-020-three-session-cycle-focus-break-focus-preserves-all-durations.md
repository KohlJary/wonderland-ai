## Scenario 020: Three-session cycle (focus→break→focus) preserves all durations

**Severity:** delight

**Setup:**

Keisha runs focus(1500s actual 1502), break(600s actual 602), focus(1500s actual 1498). All complete.

**Trigger:**

POST /sessions/log for each. Then GET /daily/summary.

**Expected:**

GET /sessions: exactly 3 sessions (no dupes, no loss). GET /daily/summary: focus_minutes≈50, break_minutes=10. No double-counting.

**Concern:**

Comprehensive sanity check. If any pipeline part breaks (idempotency, dedup, aggregation, state machine), this catches it. Aspirational test; once endpoints ready, should be first real end-to-end test. Delight because it exercises system-level properties unit tests miss.

**Property:**

For N sessions with configured [C1, C2, ..., CN] and actual [A1, A2, ..., AN]: all N logged, all unique, each actual ≤ configured + 5% (drift), daily_totals = sum(actual).

**Implies:**
- Once POST /sessions/log and daily-summary query ready, run this first.
- Canary: passes = confidence in whole flow; fails = clear repro of broken state.
- Tests system-level properties not captured by unit tests.
