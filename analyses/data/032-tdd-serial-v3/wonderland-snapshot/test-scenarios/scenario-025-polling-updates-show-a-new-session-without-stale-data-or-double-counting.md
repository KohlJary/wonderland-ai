## Scenario 025: Polling updates show a new session without stale data or double-counting

**Severity:** degradation

**Setup:**

Dmitri is viewing the daily summary (4 sessions shown, polling every 10s). At T+5s, he completes a fifth focus session. At T+10s, the frontend's polling fires and queries GET /sessions?date=2024-01-15.

**Trigger:**

Backend returns the updated list: 5 sessions now. Frontend renders the new data.

**Expected:**

The display updates to show 5 sessions. The total focus time increases. No session is shown twice. The old 4 sessions are still present in the updated list.

**Concern:**

Frontend might append the new session to the old list instead of replacing it (double-counting). Frontend might cache aggressively and not poll at all, showing stale data. The polling interval might be so fast that in-flight requests collide, showing inconsistent counts. A race condition might cause the session to appear and disappear.

**Property:**

Over a continuous polling window [T0, T_final], at any polling cycle, the displayed session count never decreases. If a new session is logged between cycles, it appears in the next cycle's response.

**Implies:**
- Implies frontend must not append polling responses; must replace the entire view on each poll.
- Implies backend query must be consistent within a single request (no partial/dirty reads where some sessions are from different physical writes).
