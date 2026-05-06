## Observation 006: Credential-stuffing attack halted; rate-limit and lockout enforcement operational

**Type:** post-deploy
**Severity:** sev1
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T15:47:00Z

**Symptom:**

Attack traffic ceased following rate-limit and lockout deployment. IP 203.0.113.42 rate-limited after exceeding 10 attempts/minute threshold; 47 user accounts locked after 5 failed attempts in 5-minute window. Telemetry shows login attempt volume returned to baseline (mean 2.3 req/sec, p95 3.8 req/sec) at T+84 minutes post-deploy. No further attack-pattern IPs detected in logs. Zero confirmed successful credential attempts during attack window (audit logs pending forensic parse per Queen ruling 002).

**Affected scope:**

/login endpoint; 47 locked accounts; 1 attacking IP (203.0.113.42); 4,127 attempted credential pairs; estimated 380 requests blocked by rate-limit before lockout engagement

**Evidence:**
- https://grafana.internal/d/auth/login-rps?from=2026-05-05T14:00Z&to=2026-05-05T16:00Z
- https://grafana.internal/d/auth/rate-limit-rejections?from=2026-05-05T14:00Z&to=2026-05-05T16:00Z
- logs: app=auth_service, level=info, event=rate_limit_exceeded, window=14:23-15:47, count=4127
- logs: app=auth_service, level=info, event=account_locked, window=14:23-15:47, count=47

**Probable domain:** security

**Routed to:** queen_of_hearts
