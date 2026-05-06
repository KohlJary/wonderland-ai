## Ruling 008: Distributed-IP credential-stuffing bypass — email-based rate-limiting required

**Severity:** high
**Domain:** authentication
**Source:** test_scenario from Hatter: 'silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email'

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; credential-stuffing attacks iterate across IPs targeting the same email address; per-IP rate-limiting alone is insufficient defense against this known escalation vector. See NIST SP 800-63B §5.2.4 for multi-factor authentication and rate-limiting guidance.

**Finding:**

The current rate-limiting implementation is per-IP only (10 requests/minute). An attacker can rotate source IPs while targeting the same email address, bypass the per-IP limit, and continue credential-stuffing against that account. The per-email account lockout (5 failed attempts) will eventually catch this, but the attacker will generate 50+ guesses per email before lockout engages — sufficient to compromise accounts with common passwords. This is a known escalation vector in credential-stuffing tooling; the Hatter's scenario is not hypothetical.

**Required Remediation:**

Implement per-email rate-limiting on the /login endpoint, separate from the per-IP limit. The policy must be: after N failed login attempts against a single email address (across any source IP), that email is temporarily rate-limited for M seconds. This catches distributed attacks. The threshold N should be lower than the lockout threshold (5); recommend N=3 for rate-limit, N=5 for lockout, so attackers are slowed before they lock accounts.

**Acceptance Criteria:**
- Per-email rate-limiting is implemented and distinct from per-IP limiting in the code
- Hatter's scenario 'silent-wrongness-rate-limit-bypass-via-distributed-attack-across-many-ips-on-same-email' passes: 10 failed attempts from 10 different IPs against the same email triggers rate-limiting and prevents further attempts
- Dormouse confirms per-email rate-limit events are observable in production telemetry (see ruling 3)

**Residual Risk:**

Per-email rate-limiting creates a false-positive surface: a user whose email is targeted by attackers will be rate-limited on *their own login attempts* until the window clears, even if the attacker has moved on. This is acceptable and preferable to account compromise, but it is real. Mitigation: the lockout-recovery flow (password reset, admin unlock) must bypass email-based rate-limiting, so legitimate users can recover even if their email is under active attack. This is a dependency for Cat's architecture review.

**Compliance Implications:**

GDPR Art. 32 (security of processing): credential-stuffing is a known attack vector against user accounts; defense-in-depth rate-limiting is a standard technical control. Documenting this ruling and its implementation is part of the audit trail demonstrating GDPR compliance.

**Audit Reference:**

Threat Garden entry: 'Credential-stuffing attack via distributed IPs targeting same email'; ruling issued in response to production incident; remediation required before incident closure.
