## Observation 003: Credential-stuffing attack: 47 users compromised; attack ongoing as of ruling publication

**Type:** incident
**Severity:** sev1
**Time window:** 2026-05-05T14:15:00Z — ongoing

**Symptom:**

Login endpoint receiving distributed credential-stuffing requests from 23 distinct IP addresses targeting 47 user accounts. 12 accounts show successful login + immediate secondary activity (API key generation, account settings modification). 35 accounts show failed attempts only. Attack is continuous; request rate to /login remains elevated. No rate-limiting currently deployed on endpoint.

**Affected scope:**

47 user accounts (12 with evidence of compromise, 35 with failed-attempt pattern only). /login endpoint. Attack traffic is originating from 23 distinct IPs across 6 geographic regions; legitimate user impact is indirect (account lockout due to failed-attempt threshold, not direct compromise).

**Evidence:**
- https://grafana.internal/d/auth/login-endpoint?from=2026-05-05T14:15:00Z&to=now — request rate, error rate, geographic distribution of source IPs
- logs: app=auth, endpoint=/login, level=warn|error, time=14:15-now — failed login attempts, geographic clustering, account targeting patterns
- trace sample: auth-login-20260505-232847-01HXY... — successful login from unusual IP immediately followed by auth-key-generation
- database audit log: user_id in (445, 623, 712, ...) [12 users], action=api_key_create|settings_update, timestamp within 2min of successful login from non-baseline IP

**Probable domain:** backend

**Routed to:** tweedledum
