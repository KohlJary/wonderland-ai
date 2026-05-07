## Scenario 003: Session timeout fires server-side while client offline; reconnection sees completed state

**Severity:** degradation

**Setup:**

Marcus starts 25-min session, after 20 min goes offline. At +25 min, session times out server-side. At +26 min, reconnects.

**Trigger:**

Client polls /session/current after reconnect.

**Expected:**

/session/current returns {state: 'completed', completed_at: <timestamp>}. Client UI transitions to break flow.

**Concern:**

If server doesn't track timeout independently, session stays active forever. Client's local timer keeps counting. Stale data on reconnect.

**Property:**

For all active sessions, if (now_server - start_time) >= duration_minutes * 60, session.state must be 'completed'.
