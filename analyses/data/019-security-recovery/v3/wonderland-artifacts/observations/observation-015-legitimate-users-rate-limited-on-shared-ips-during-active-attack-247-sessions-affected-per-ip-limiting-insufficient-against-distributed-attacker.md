## Observation 015: Legitimate users rate-limited on shared IPs during active attack; 247 sessions affected; per-IP limiting insufficient against distributed attacker

**Type:** incident
**Severity:** sev2
**Time window:** 2024-12-19T14:23:00Z — 2024-12-19T14:58:00Z

**Symptom:**

Per-IP rate limiter (10 req/min, 60s sliding window) triggered before per-email lockout engaged. Legitimate users on shared corporate/university/office networks experienced 429 Too Many Requests errors during attack window. Total affected: 247 user sessions on IPs with concurrent attacker traffic. No account compromise; sessions recovered within 60s or via network change. Attack vectors on same IPs continued undetected until per-email lockout accumulated 5 failures per target account.

**Affected scope:**

247 legitimate users on shared IPs (x.x.x.0/24, y.y.y.0/24, z.z.z.0/24); 14:23–14:58 UTC; auth endpoint /login only

**Evidence:**
- Dashboard: auth_service/rate_limit_events, filtered source_ip IN (x.x.x.0/24, y.y.y.0/24, z.z.z.0/24), time 14:23-14:58
- Logs: http 429 responses, source IPs above, timestamp range 14:23-14:58, count=1247
- Session table: SELECT COUNT(*) FROM sessions WHERE created_at < '2024-12-19T14:23:00Z' AND (last_activity > '2024-12-19T14:23:00Z' OR logout_at IS NULL) AND source_ip IN (corporate/university/office ranges); estimate 247 sessions
- FailedAttempt logs: attack attempts on 14 distinct email targets from IPs above, 5+ failures per target by 14:47:00Z (lockout threshold)

**Probable domain:** backend, observability, user experience

**Routed to:** alice
