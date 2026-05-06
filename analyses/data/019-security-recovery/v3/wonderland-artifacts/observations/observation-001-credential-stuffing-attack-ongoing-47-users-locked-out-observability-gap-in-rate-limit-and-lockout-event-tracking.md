## Observation 001: Credential-stuffing attack ongoing; 47 users locked out; observability gap in rate-limit and lockout event tracking

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:15:00Z — ongoing

**Symptom:**

Failed login attempts on auth service spike from ~12/min baseline to 847/min starting 14:15 UTC, sourcing from single IP 203.0.113.42. Request pattern matches credential-stuffing signature: rotating username attempts, consistent password. After initial mitigation (manual IP block at 14:23), attack shifted to distributed pattern across 18 source IPs targeting same 47 email addresses. Account lockout triggered for these users at 14:31 UTC. Current state: 47 users unable to log in; attack continues on remaining email corpus at elevated rate (312/min); no automated rate-limit or lockout instrumentation in place to track event velocity or distribution.

**Affected scope:**

Auth service, 47 user accounts (locked), email namespace under active attack (remaining ~4.2M accounts at risk if attack pattern expands). Legitimate user access blocked for locked accounts.

**Evidence:**
- https://grafana.internal/d/auth-service/login-attempts?from=2026-05-05T14:00:00Z&to=2026-05-05T15:00:00Z — failed login attempt rate, source IP distribution
- https://logs.internal/auth?service=login&level=error&window=2026-05-05T14:15:00Z,2026-05-05T15:00:00Z&query=failed_login — 12,847 failed attempts in 45-minute window; 847/min peak at 14:15-14:23; 312/min sustained after 14:31
- Access logs: IP 203.0.113.42, 623 attempts in 8 minutes (14:15-14:23); distributed attack, 18 IPs, 224 attempts/min (14:31-14:45)
- Account status query: 47 accounts with locked_at timestamp between 14:31-14:32 UTC; locked_reason='repeated_failed_login'
- Alert: Queen's security monitoring flagged pattern at 14:18 UTC (3min lag); manual escalation at 14:23; distributed shift detected at 14:31

**Probable domain:** backend

**Routed to:** tweedledum
