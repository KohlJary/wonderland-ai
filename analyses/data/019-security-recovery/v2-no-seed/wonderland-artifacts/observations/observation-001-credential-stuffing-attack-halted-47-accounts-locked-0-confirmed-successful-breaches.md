## Observation 001: Credential-stuffing attack halted; 47 accounts locked, 0 confirmed successful breaches

**Type:** post-incident-confirmation
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T15:47:00Z

**Symptom:**

Attack ceased following rate-limit deployment at 15:42 UTC. Login endpoint request volume returned to baseline (8–12 req/s, mean latency 45ms). Failed-login event count dropped from 847/min to <2/min. 47 unique accounts hit the 10-attempt lockout threshold during the attack window. Query of auth logs for the 4,127 attempted credentials (timestamped 14:23–15:42) shows 0 successful authentications.

**Affected scope:**

Login endpoint (/auth/login). 47 user accounts locked. No confirmed account compromise.

**Evidence:**
- https://grafana.internal/d/auth/login-volume?from=2026-05-05T14:00:00Z&to=2026-05-05T16:00:00Z (rate-limit deployment visible at 15:42; volume drop immediate)
- Prometheus query: rate(auth_failed_login_attempts_total[1m]) from 14:23–15:47 UTC (peak 847/min at 15:38, baseline <2/min by 15:50)
- auth.log: grep 'failed_login' 2026-05-05T14:23:00Z–2026-05-05T15:42:00Z | wc -l = 4127 attempted; grep 'successful_login' same window = 0 matches
- Dashboard: /auth/lockout-status shows 47 accounts in LOCKED_OUT state as of 15:47 UTC

**Probable domain:** security

**Routed to:** queen_of_hearts
