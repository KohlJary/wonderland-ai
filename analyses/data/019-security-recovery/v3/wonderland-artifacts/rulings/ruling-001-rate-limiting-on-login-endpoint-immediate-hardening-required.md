## Ruling 001: Rate-limiting on /login endpoint — immediate hardening required

**Severity:** critical
**Domain:** authentication
**Source:** Dormouse observation of ongoing credential-stuffing attack; 4,127 failed attempts in 8 minutes from single source

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames; CWE-770 Allocation of Resources Without Limits or Throttling. Industry standard: brute-force protection via rate-limiting is foundational auth defense.

**Finding:**

Endpoint /login has no per-source-IP rate-limiting. Active attack demonstrates exploitation: 4,127 attempts in 8 minutes is trivial for automated tooling. Without rate-limiting, attacker will continue; lockout threshold (currently 5) will exhaust against legitimate users. Breach of authentication integrity is in progress.

**Required Remediation:**

Per-source-IP rate-limiting must be deployed to /login endpoint before the attack window closes. Shape: reject further login attempts from any IP that has exceeded 10 failed attempts within any 15-minute window, returning HTTP 429 (Too Many Requests). The IP is rate-limited for 15 minutes from the last failed attempt, then counter resets. This shape: (a) stops the current attack immediately by triggering on the attacker's established request volume, (b) permits legitimate users with transient network issues to retry within a reasonable window, (c) is orthogonal to account-lockout (see next ruling).

**Acceptance Criteria:**
- Rate-limiting is deployed to production /login endpoint
- Dormouse confirms in production telemetry: requests from 203.0.113.42 are returning 429 within 2 minutes of ruling shipment
- Legitimate login attempts from distinct IPs with <10 failures per 15min are not rate-limited
- Rate-limit headers (Retry-After, X-RateLimit-*) are present in 429 responses

**Residual Risk:**

Rate-limiting at endpoint level can be bypassed by distributed attacks (attacker spoofs source IPs or uses botnet). This residual is acceptable short-term; it buys time. Long-term, the system needs WAF-level rate-limiting and CAPTCHA on login after N failures (Hatter scenario, Tweedles implementation, post-incident). Document and schedule.

**Compliance Implications:**

Not directly compliance-triggered, but the ongoing attack may breach user accounts, which triggers breach-notification obligations (see separate ruling).

**Audit Reference:**

Rate-limiting deployment log; production telemetry during and after 429 threshold crossing
