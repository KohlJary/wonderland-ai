## Ruling 014: Password-reset endpoint must have separate rate-limit policy from login

**Severity:** high
**Domain:** authorization
**Source:** proposal from Cheshire Cat; scenario 5 from Mad Hatter

**Citation:**

CWE-307 Improper Restriction of Rendered UI Layers or Frames; OWASP A01:2021 Broken Access Control. Users locked by attack must be able to initiate account recovery without hitting the same rate limiter that locked them. Sharing rate-limit namespace between login and password-reset creates a false lockout for legitimate recovery attempts.

**Finding:**

The ADR correctly identifies the seam: password-reset flows must bypass or separate from the login rate limiter, otherwise users locked by attack cannot self-recover. The current implementation treats all email-lookup requests identically. When /password-reset ships (confirmed out-of-scope for v1), it will either share the rate limiter (locking users out of recovery) or bypass it entirely (opening a secondary attack surface). Neither is acceptable.

**Required Remediation:**

Before /password-reset ships in any future version, it must have an explicit rate-limit policy separate from the login endpoint. The policy must allow authenticated password-reset requests to proceed even if the email address has triggered login-endpoint rate limiting. The implementation must distinguish password-reset email lookups from login email lookups in the rate-limit namespace.

**Acceptance Criteria:**
- When a user is locked by account-lockout, they can initiate password recovery without hitting the login rate limiter
- Password-reset endpoint has its own rate-limit policy (separate thresholds or grace period for locked accounts)
- Implementation distinguishes password-reset requests from login requests in the rate-limit decision logic

**Residual Risk:**

Until /password-reset is implemented, this risk is deferred. When it ships, the implementation must address this seam immediately; shipping with shared rate-limit logic would create a compliance gap (users unable to recover compromised accounts).

**Compliance Implications:**

GDPR Art. 32 (security of processing). Users must be able to recover compromised accounts. A system that locks users out of recovery is a security control that has become a security barrier.

**Audit Reference:**

Ruling: Password-reset endpoint rate-limiting must isolate from login rate-limiting. Deferred implementation; contract required before /password-reset ships.
