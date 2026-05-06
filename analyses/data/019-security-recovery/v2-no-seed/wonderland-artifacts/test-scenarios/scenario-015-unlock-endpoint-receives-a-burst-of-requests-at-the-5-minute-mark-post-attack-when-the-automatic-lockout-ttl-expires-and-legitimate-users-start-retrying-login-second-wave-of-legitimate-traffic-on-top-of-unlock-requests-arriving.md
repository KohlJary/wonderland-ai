## Scenario 015: Unlock endpoint receives a burst of requests at the 5-minute mark post-attack when the automatic lockout TTL expires and legitimate users start retrying login (second wave of legitimate traffic) on top of unlock requests arriving

**Severity:** curiosity

**Setup:**

The lockout duration is 15 minutes (per the implementation). The attack window was 8 minutes. The rate-limit and lockout code deployed at T+8min. At T+23min, the first batch of locked-out users can attempt login again (15-minute TTL expired). They do. Simultaneously, unlock emails are still arriving (batched send, SLA of 5 minutes), and users are clicking unlock links. The /login endpoint gets a spike of legitimate retries. The /unlock endpoint gets a spike of token validations and session creations. Both happen at the same second. Database connection pool, email service, session store, and audit log all experience bursty load.

**Trigger:**

T+23 minutes post-attack: automatic lockout TTL expires for the first cohort. They retry login. /unlock endpoint processes token validations. Both surge simultaneously.

**Expected:**

Both endpoints degrade gracefully. /login retries queue; users see a 503 Service Unavailable with Retry-After. /unlock processes queued requests without dropping tokens or losing audit trail. No data loss. No unlogged sessions.

**Concern:**

The system was designed for incident response (in-memory stores, no connection pooling for audit trail, single-threaded session validation). The load at T+23 is predictable but not controlled — we cannot tell users 'wait until 4pm to retry.' If the infrastructure was sized for baseline load, the surge at T+23 might cause cascading failures (dropped audit logs = Queen's investigation is incomplete, dropped session validations = attacker sessions are not recorded).

**Property:**

For all requests processed during the T+23 load spike, there is no data loss: every login attempt is recorded in audit_log, every session is persisted to audit trail, every unlock token validation is logged. Latency may degrade (p99 goes from 45ms to 500ms), but no request fails due to missing audit trail capacity.

**Implies:**
- Implies operational load-testing and capacity-planning requirement (Dormouse should observe and alert on audit trail saturation; Tweedles should validate that in-memory stores handle the T+23 spike without overflow).
