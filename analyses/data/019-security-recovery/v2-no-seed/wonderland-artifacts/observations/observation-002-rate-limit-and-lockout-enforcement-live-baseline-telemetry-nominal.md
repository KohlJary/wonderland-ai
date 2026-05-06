## Observation 002: Rate-limit and lockout enforcement live; baseline telemetry nominal

**Type:** post-deploy
**Severity:** sev2
**Time window:** 2026-05-05T14:47:00Z — ongoing

**Symptom:**

Tweedledum's auth_service.py and http_middleware.py deployed to production. IP 203.0.113.42 rate-limited after 10 attempts/minute threshold crossed (currently 47 requests blocked in last 3 minutes). Account lockout state machine engaged: 23 accounts in locked state, 4 in cooldown, 0 failures on currently-enforced 5-per-5min threshold. Error response latency 12ms (baseline 8ms), within tolerance. No auth service crashes, no middleware exceptions logged.

**Affected scope:**

All /login requests globally. Current impact: 203.0.113.42 (attack origin) fully blocked. 23 locked-out legitimate users (per Queen's ruling: notification due within 30 minutes). 4 users in 5-minute cooldown.

**Evidence:**
- https://grafana.internal/d/auth-incident/rate-limit-enforcement?from=2026-05-05T14:47:00Z
- logs: app=auth_service, component=rate_limit_handler, window=last-5m, event_count=127
- logs: app=http_middleware, endpoint=/login, status=429, window=last-5m, count=47
- logs: app=auth_service, component=lockout_state_machine, locked_accounts=23, cooldown=4

**Probable domain:** backend

**Routed to:** tweedledum
