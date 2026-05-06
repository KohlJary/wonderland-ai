## Observation 005: Rate-limit and lockout observability contract missing before implementation; risk of non-observable mitigation

**Type:** anomaly
**Severity:** sev2
**Time window:** 2026-05-05T15:00:00Z — ongoing

**Symptom:**

Tweedles are beginning implementation (tickets are active) without signed contract on rate-limit/lockout observability. Rate-limit decisions are happening in backend code; lockout decisions are happening in backend code. If these events are not instrumented *during* implementation with the right granularity (per-IP, per-email, per-account, success/failure/suppressed distinction), production telemetry will be insufficient to detect the next attack vector (distributed-IP, email-based targeting, etc.). Re-instrumenting after the fact produces blind spots between implementation and instrumentation deployment.

**Affected scope:**

Observability of rate-limiting and account-lockout behavior; future incident detection.

**Evidence:**
- Mad Hatter scenario: slug=silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email — identifies distributed-IP attack as likely escalation
- White Rabbit concern: observability-debt point — 'Dormouse should own it' but 'should be on the board now'
- implementation tickets in progress; no contract note from Dormouse to Tweedles on observability shape

**Probable domain:** backend

**Routed to:** tweedledum
