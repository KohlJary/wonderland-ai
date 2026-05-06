## Ruling 006: Password-reset endpoint rate-limiting — must not lockout legitimate password-recovery flow

**Severity:** high
**Domain:** authentication
**Source:** test_scenario from Mad Hatter (lockout-escape-hatch-legitimate-password-reset-flow-must-not-be-rate-limited)

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; threat model: account lockout must have a legitimate escape hatch; if /password-reset shares rate-limit logic with /login, locked-out users cannot exit lockout state, and /password-reset becomes a secondary credential-stuffing vector (reset-spam + account takeover).

**Finding:**

If the /password-reset endpoint uses shared rate-limiting logic with /login, or if rate-limiting is applied to password-reset at all, then: (a) locked-out users cannot reset their way out of lockout, creating a denial-of-service condition for legitimate users; (b) the /password-reset endpoint itself becomes a secondary attack vector (automated password-reset-spam to lock users out of account recovery); (c) attackers can use the password-reset flow to enumerate valid email addresses at scale. If /password-reset is not yet implemented, it must be implemented with separate, email-specific rate-limiting that does *not* share state with login rate-limiting.

**Required Remediation:**

If /password-reset endpoint exists: audit its rate-limiting logic immediately. If it shares state or thresholds with /login rate-limiting, separate it. Password-reset should be rate-limited per email address only (not per IP), with a higher threshold than login (recommendation: 5 reset attempts per email per hour), and reset-limit state must be independent of login-limit state. If /password-reset is not yet implemented: implement it with separate email-based rate-limiting from the start (do not inherit login rate-limit logic).

**Acceptance Criteria:**
- Code audit confirms /password-reset endpoint (if it exists) does not share rate-limit state or thresholds with /login
- If /password-reset exists and was using shared logic, it is refactored to use separate email-based rate-limiting
- If /password-reset does not exist, implementation includes explicit email-based rate-limiting separate from login logic
- Hatter's scenario 'lockout-escape-hatch-legitimate-password-reset-flow-must-not-be-rate-limited' passes
- Integration test confirms locked-out user can trigger password-reset flow without hitting rate-limit

**Residual Risk:**

Password-reset endpoints have their own attack surface (account enumeration via reset-spam, reset-token prediction). Separate rate-limiting reduces but does not eliminate this. Accepted: residual enumeration risk is lower-severity than lockout-escape-hatch denial-of-service.

**Compliance Implications:**

None direct. Account lockout without legitimate recovery path may violate accessibility expectations (WCAG 2.1); the escape hatch is required for defensible UX.

**Audit Reference:**

incident-response thread: password-reset rate-limiting audit and refactor (if applicable)
