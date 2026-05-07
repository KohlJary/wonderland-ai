## Scenario: Client's local clock drifts; system reconciles using server time

**Severity:** degradation

**Setup:**
Marcus starts a 25-minute session. The client caches session start_time and remaining_seconds from /session/current. Meanwhile, Marcus's phone's clock is 3 seconds fast (maybe he synced to the wrong NTP server). The client timer is therefore showing 3 seconds fewer remaining than the server thinks.

**Trigger:**
Marcus taps 'Refresh' (or the client auto-polls after 5 seconds, per contract), requesting /session/current again while the clock skew persists.

**Expected:**
The backend computes remaining_seconds using server time. The response shows remaining_seconds that reflects the true server state, not the skewed client state. The client detects that its computed remaining diverges >5s from the server remaining and re-syncs its local state.

**Concern:**
If the client never reconciles with server time:
- The countdown on-screen will slowly diverge from reality
- When the user's local clock hits zero, their local timer fires a notification
- But the server hasn't completed the session yet, so the server fires its own notification 3 seconds later
- The user gets two notifications, or a notification too early
- This is degradation (not breakage) because the system still technically works, but the UX is confusing and untrustworthy

**Property:**
For any session S:
- If client remaining_seconds deviates from (server remaining_seconds) by > 5 seconds, client re-syncs from server value
- Client never displays a remaining time that is less than the server's remaining time minus client-polling-latency

**Implies:**
- Implies frontend: client-side timer logic must reconcile with /session/current polling
- Implies contract: specify the tolerance threshold (contract says 5s; confirm this is sufficient for typical polling intervals)
