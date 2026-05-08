## Test Scenario 006: Three-session cycle (focus→break→focus) preserves all durations

**Severity:** delight

**Setup:**

Keisha runs through a complete work cycle:
1. Focus session: configured=1500s (25 min), actual=1502s (clock drift +2s)
2. Break session: configured=600s (10 min), actual=602s (clock drift +2s)
3. Focus session: configured=1500s (25 min), actual=1498s (clock drift -2s)

All three sessions complete successfully. She checks her daily summary: does it show 50 minutes of focus + 10 minutes of break?

**Trigger:**

- POST /sessions/log { type: 'focus', duration_configured: 1500, duration_actual: 1502, ... }
- POST /sessions/log { type: 'break', duration_configured: 600, duration_actual: 602, ... }
- POST /sessions/log { type: 'focus', duration_configured: 1500, duration_actual: 1498, ... }
- GET /daily/summary?date=YYYY-MM-DD

**Expected:**

- GET /sessions?date=YYYY-MM-DD returns exactly 3 sessions (1 break, 2 focus), no duplicates
- GET /daily/summary?date=YYYY-MM-DD returns:
  - focus_minutes ≈ 50 (1500 + 1500) / 60
  - break_minutes = 10 (600 / 60)
  - Sessions are not double-counted or lost

**Concern:**

This is a comprehensive sanity check. If any part of the pipeline is broken (idempotency, deduplication, aggregation, state machine), this test catches it. It's also the "happy path" that should always pass; if it doesn't, the entire feature is broken.

The delight here is that the test exercises the full cycle. It's not just "one session logs correctly" — it's "the whole day's worth of sessions logs, and the daily summary adds up."

**Property:**

For a sequence of N sessions with configured_durations [C1, C2, ..., CN] and actual_durations [A1, A2, ..., AN]:
- All N sessions are logged (no loss)
- All N sessions are unique (no duplicates)
- Each session's actual duration A_i is within 5% of configured C_i (clock-drift tolerance)
- Daily totals: sum(actual_durations) = sum(A_i) (no arithmetic errors in aggregation)

**Implies:**

This test is aspirational for a feature that's not fully implemented yet. Once POST /sessions/log is ready and the daily-summary query is in place, this should be the first real end-to-end test to run. It's a canary: if it passes, you have confidence in the whole flow. If it fails, you have a clear reproduction of the broken state.

It's a delight scenario because it exercises system-level properties that aren't captured by unit tests of individual endpoints.
