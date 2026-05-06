## Ruling 004: Rate-limit /login endpoint to halt ongoing credential-stuffing attack

**Severity:** critical
**Domain:** input-validation
**Source:** observation from Dormouse; incident-response thread

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames; active threat signature: high-volume login attempts from single IP across distinct usernames with 94% failure rate over 8-minute window.

**Finding:**

Attacker is iterating through a leaked-credentials list against /login endpoint at ~500 attempts/minute from single source IP (203.0.113.42). At current rate, the attacker will exhaust a 1M-credential list in ~33 hours. Already 47 user accounts locked out; if attack continues, account-lockout feedback becomes a secondary attack surface (account enumeration). The attack is active now; halting it requires operational change within the next 60 minutes.

**Required Remediation:**

Implement rate-limiting on /login endpoint that (a) blocks further login attempts from source IP after N failed attempts within M-minute window, (b) applies per-IP not per-credential (to prevent attacker from bypassing via credential rotation), (c) resets the failure counter on successful login (to avoid collateral-locking legitimate users), (d) surfaces rate-limit rejection with HTTP 429 and a clear message to the client, (e) logs every rate-limit trigger event to audit trail with source IP, attempted username, and timestamp.

**Acceptance Criteria:**
- Rate-limit rule deployed to production and active on /login endpoint
- Dormouse confirms telemetry shows no login attempts from 203.0.113.42 for last 10 minutes
- No legitimate-user login failures attributable to rate-limit (audit trail shows zero 429 responses from known-good corporate IP ranges, home ISPs of users who logged in successfully during attack window)
- Caterpillar confirms rate-limit implementation does not introduce timing side-channels that enable secondary username enumeration

**Residual Risk:**

Attacker can rotate source IP to resume attack from different origin. This is acceptable short-term (rate-limit halts the immediate attack); long-term remediation is the Hatter's monitoring scenarios and the post-incident threat model update. Accepting residual IP-rotation attack risk for the next 48 hours while post-incident hardening ships.

**Compliance Implications:**

GDPR Art. 32 (security of processing) — credential-stuffing attack represents a failure of access controls. Rate-limit deployment is the immediate control; the post-incident threat model and monitoring update are the evidence that the failure has been addressed systemically.

**Audit Reference:**

Incident-response thread, Queen ruling #1. Audit trail entries: every rate-limit trigger with source IP and timestamp; successful revert/disable of rate-limit after attack window (to avoid false-positive collateral lockout post-incident); post-incident threat model review with Hatter scenario coverage.
