## Scenario 018: Successful-login events during attack window are indistinguishable from normal logins — breach-notification ruling cannot execute

**Severity:** silent-wrongness

**Setup:**

A credential-stuffing attack occurs. Some credentials succeed (user's real password was in the leaked list). The rate limiter lets those requests through because they have valid credentials. A successful login is indistinguishable in the telemetry from a successful login on a quiet Tuesday. The FailedAttempt table logs failures; successful logins are written to the Session table, but there is no flag, no metric, no marker saying 'this successful login occurred during the attack window (14:30-15:45 UTC)'.

**Trigger:**

Post-incident analysis: the Dormouse tries to determine which accounts to notify per the Queen's breach-notification ruling. Query: 'give me all successful logins during the attack window (14:30-15:45 UTC on 2024-01-15).' The Session table has no way to distinguish these from normal sessions.

**Expected:**

Successful logins are observable with temporal context. Either (a) successful logins are logged as events with timestamp, (b) session creation includes metadata flagging the risk window, or (c) a separate 'SuccessfulAttemptDuringAttack' table tracks credentials that succeeded while rate limiting was active.

**Concern:**

The Queen's ruling #4 requires breach notification for 'any account where attack succeeded'. Without observability for successful login *during the attack window*, the team cannot determine which accounts to notify. The ruling becomes unexecutable. This is silent wrongness—the system looks functional, but it cannot fulfill compliance obligations.

**Property:**

For all authentication events (success or failure), the observability must include sufficient context (timestamp, source_ip, email, reason) such that post-incident queries can answer: 'which accounts succeeded during [time window]?'

**Implies:**
- Implies that session creation must include observability hooks. Currently Session.make() has no connection to rate-limit context or attack-window markers. The Tweedles and Dormouse must negotiate a contract for how successful logins are marked/logged during active rate-limiting.
- Implies that the breach-notification work (Alice's story) cannot proceed until this observability is in place. It is a blocking dependency.
