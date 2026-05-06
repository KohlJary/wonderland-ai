## Ruling 001: Rate-limit /login endpoint to halt credential-stuffing attack

**Severity:** critical
**Domain:** input-validation
**Source:** observation from Dormouse: 4,127 failed attempts in 8 minutes from single IP, 0.2% success rate, 47 accounts locked

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames; threat model: brute-force / credential-stuffing attack via /login endpoint. The observed pattern (high-volume, rotating User-Agent, distinct usernames, single source IP) is signature credential-stuffing behavior. Unmitigated, the attack will continue exhausting the lockout threshold across the user population.

**Finding:**

The /login endpoint has no per-IP rate-limiting. An attacker with a leaked-credentials list can iterate through usernames at scale without degradation. The 4,127 attempts in 8 minutes demonstrates the attack is actively in progress. If unmitigated: (1) all accounts in the attacker's list will eventually be attempted; (2) account lockouts will proliferate, creating a denial-of-service effect on legitimate users; (3) any successful credentials grant the attacker account access, potentially to further systems; (4) the attack will continue until the attacker exhausts the list or is manually blocked.

**Required Remediation:**

Implement per-IP rate-limiting on /login endpoint. Threshold: max 10 failed login attempts per IP per 15-minute window. When threshold is crossed, return HTTP 429 (Too Many Requests) and block further /login attempts from that IP for 15 minutes. This must: (1) stop the attack source immediately (203.0.113.42 will hit threshold on attempt ~11 and cease); (2) allow legitimate users to retry after the window expires; (3) not interfere with users behind shared IPs (coffee shops, corporate networks) — use the existing user-agent + IP combination as the rate-limit key if per-IP alone causes collateral damage, but per-IP alone is preferred for simplicity in an active incident. (4) Log every rate-limit trigger to the audit trail with source IP, timestamp, and attempt count at time of blocking.

**Acceptance Criteria:**
- Rate-limit middleware is deployed to /login in working tree and tested locally to block requests after 10 failures in 15-minute window
- HTTP 429 response is returned to rate-limited clients with Retry-After header set to seconds-until-window-reset
- Audit log entry recorded for every rate-limit trigger, queryable by source IP
- Production deployment: source IP 203.0.113.42 receives 429 on next request attempt and ceases further attempts (confirm via Dormouse observation of traffic drop within 5 minutes of deployment)
- Legitimate users can still log in after the 15-minute window (no permanent IP bans; only window-based throttle)

**Residual Risk:**

Rate-limiting per-IP does not prevent attacks from distributed sources (botnet with many IPs). This is acceptable for immediate incident response because: (1) the current attack is single-source; (2) implementing distributed-source defenses (CAPTCHA, email verification, device fingerprinting) is medium-term work; (3) the rate-limit buys time for the medium-term defenses. Record this as an authorized residual risk (see Threat Garden §IX) with expiry of 30 days — if distributed credential-stuffing attacks materialize within that window, revisit.

**Compliance Implications:**

GDPR Art. 32(1)(b) requires technical measures to ensure security of processing. Rate-limiting on authentication endpoints is a standard technical measure. If any of the 4,127 attempts succeeded (we do not yet know), the compromised accounts may constitute a personal data breach under GDPR Art. 33 (notification to supervisory authority within 72 hours) and Art. 34 (notification to data subjects). Dormouse's observation does not confirm successful breaches yet; this must be investigated (see separate ruling below). If confirmed, breach notification is mandatory.

**Audit Reference:**

incident-response thread, credential-stuffing, ruling issued at [timestamp], rate-limit implementation tracked in Threat Garden under 'Credential-stuffing: 203.0.113.42'
