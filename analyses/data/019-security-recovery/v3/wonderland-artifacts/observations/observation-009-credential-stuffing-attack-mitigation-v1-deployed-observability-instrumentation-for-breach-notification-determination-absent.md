## Observation 009: Credential-stuffing attack: mitigation v1 deployed; observability instrumentation for breach-notification determination absent.

**Type:** post-deploy
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T16:45:00Z

**Symptom:**

Rate-limiting and account lockout controls are live on /login. Per-IP rate-limiter (10 req/min) and per-email lockout (5 failures) are operational and suppressing the attack. Attack velocity has declined from ~2,400 attempts/min (14:23 UTC) to ~140 attempts/min (16:30 UTC); lockout count stabilized at 47 users. However, the implementation ships no instrumentation for successful-login events during the attack window. The Queen's ruling on breach-notification determination requires knowing which credentials succeeded in the attack; without telemetry on successful authentications, that determination cannot be made. Rate-limit and lockout events are not currently observable in production—no metrics, no audit trail beyond the in-memory counters. This is a compliance blocker for v1 per the Queen's ruling #3.

**Affected scope:**

/login endpoint; authentication service; breach-notification work (blocked pending observability)

**Evidence:**
- Grafana dashboard auth/login-rate-limit: showing 10 req/min limit enforcement, 429 returns rising from 0 to ~340/min between 14:23-14:50, then declining to ~12/min by 16:30
- Grafana dashboard auth/account-lockout: showing lockout events, count at 47, no unlock events (lockouts remain active)
- src/auth/rate_limit.py: rate-limit checks logged to stderr, no metrics emission; no hooks for successful-login events
- src/auth/account_lockout.py: lockout state maintained in-memory (LRU cache), no event emission or audit trail
- Queen's ruling #3 (breach-notification observability): 'Production telemetry required before v1 ship' — requirement is not met by current implementation

**Probable domain:** backend

**Routed to:** tweedledum
