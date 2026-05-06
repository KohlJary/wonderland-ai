## Ruling 013: Email-token-based account unlock is the selected recovery primitive for incident response

**Severity:** critical
**Domain:** authentication
**Source:** team discussion of account-recovery options (turns 8-15); needs selection to unblock unlock-UX implementation

**Citation:**

OWASP A07:2021 Identification and Authentication Failures — account recovery must use a factor the attacker does not control. Email ownership is sufficient for v1.

**Finding:**

The team has proposed three account-recovery primitives (email-token, SMS OTP, security-question) but has not selected which one to implement in v1. Without selection, the Tweedles cannot finalize unlock-UX contracts. The locked-out users remain blocked.

**Required Remediation:**

Implement email-token-based unlock: (1) Generate a cryptographically-secure token on unlock request; (2) Send token via email to the account's registered address; (3) Validate token and issue authenticated session without re-authenticating with password; (4) Rate-limit unlock attempts to prevent brute-force of the token endpoint.

**Acceptance Criteria:**
- Email-token generation endpoint deployed and live
- Email-token validation endpoint deployed and live
- Unlock endpoint is rate-limited (max 5 attempts per account per hour)
- Token TTL is 30 minutes
- Successful token validation issues a session without requiring password re-entry
- Email delivery works in staging + production
- Token validation latency is <100ms

**Residual Risk:**

Email delivery is out-of-band; if user's email is unreachable or compromised, self-service unlock fails and support escalation is required. This is acceptable for v1. SMS fallback can be fast-follow.

**Compliance Implications:**

GDPR Art. 32 — email-token unlock is a defensible account-recovery mechanism for credential-stuffing aftermath. No additional compliance requirements triggered by this choice.

**Audit Reference:**

Ruling-013: Email-token-based unlock selected as v1 recovery primitive, 72-hour audit window opens for breach investigation.
