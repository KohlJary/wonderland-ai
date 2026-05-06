## Observation 017: Legitimate-user rate-limiting on shared IPs during attack; per-IP limiting insufficient against distributed attacker; Alice's four stories define user-facing scope of breach-notification ruling

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T14:23:00Z — 2026-05-05T17:15:00Z

**Symptom:**

Between 14:23–14:58 UTC (peak attack window), 247 legitimate user sessions were rate-limited (429 Too Many Requests) on IPs with concurrent attacker traffic (corporate networks, university IPs, shared office spaces). Users experienced service-unavailability-like errors with 60-second retry windows. Per-IP rate limit (10 req/min threshold) fired before per-email lockout on attacker accounts could fully propagate. No lasting account damage; all sessions recovered within incident window. However, Alice's four user stories (account-lockout notification, rate-limited status messaging, breach-notification clarity, account-lockout recovery flow) define user-facing scope that Queen's rulings now lock as v1-blocking. Current implementation ships no user-facing messaging for either rate-limit or lockout decisions.

**Affected scope:**

247 legitimate users on 3 shared IP ranges during attack window. User-facing messaging absent for rate-limit (429) and account-lockout (423) responses. Breach-notification messaging (Queen ruling) requires distinguishing attack-derived lockouts from user-error lockouts (not possible without observable successful-login events during attack window).

**Evidence:**
- Dormouse observation: 'Legitimate users rate-limited on shared IPs during attack' (247 sessions)
- Alice stories: account-lockout notification, rate-limited messaging, breach-notification clarity, lockout recovery flow
- Queen rulings: user-notification-related requirements now v1-blocking
- Hatter scenario #3: 'legitimate user on shared IP during attack should not be permanently locked out' (mitigation correct, but user messaging absent)
- Implementation ship: no 429/423 response body messaging; no user-facing guidance

**Probable domain:** frontend, user-experience, observability

**Routed to:** tweedledee
