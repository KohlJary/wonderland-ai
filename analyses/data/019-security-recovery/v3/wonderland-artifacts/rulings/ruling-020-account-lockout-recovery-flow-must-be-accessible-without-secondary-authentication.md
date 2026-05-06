## Ruling 020: Account-lockout recovery flow must be accessible without secondary authentication

**Severity:** high
**Domain:** authorization
**Source:** story slug=user-locked-out-by-credential-stuffing-attack-needs-to-know-why-and-how-to-recover

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-307 Improper Restriction of Rendered UI Layers or Frames. When an account is locked due to attack, the user must be able to recover without requiring secondary authentication (which they cannot provide, because their account is locked). If password-reset requires answering security questions, or if account-unlock requires confirming a phone number, locked-out users are permanently denied recovery and cannot regain control of their accounts.

**Finding:**

The current implementation locks accounts after 5 failed login attempts and provides no direct unlock mechanism. A user locked out by the attack can attempt to reset their password via the /password-reset endpoint (which does not yet exist in scope). But if the password-reset flow requires the user to verify their identity via security questions, SMS code, or email confirmation, and if those verification channels are also compromised in the attack or inaccessible, the user remains locked out. The requirement to 'change password to recover' becomes 'prove you own the account' becomes 'you're locked out' in a circular dependency.

**Required Remediation:**

Account-lockout recovery must be possible via a single factor that is already established at account-creation time. Email-based password reset (sent to the registered email address) is acceptable as a single-factor recovery mechanism, with the assumption that the registered email is less likely to be compromised than the password. SMS-based or security-question-based recovery is not acceptable as the only path during an active attack. The password-reset endpoint must not require secondary authentication (no 'confirm you're you' via phone or security question). The reset link or code must have a short expiry (e.g., 1 hour) and be single-use to prevent long-term attack surface.

**Acceptance Criteria:**
- Password-reset endpoint exists and is accessible to locked-out users
- Password-reset flow requires only email verification (link sent to registered email, valid for 1 hour, single-use)
- Password-reset does not require security questions, phone confirmation, or other secondary factors
- After successful password reset, the account is unlocked and the user can immediately log in with the new password
- User testing confirms locked-out users can recover within 5 minutes using only email

**Residual Risk:**

If an attacker compromises both the account and the registered email, they can reset the password. This is a residual risk inherent to email-based recovery. It is mitigated by the rate-limiting and lockout controls that prevent the attacker from logging in immediately after the reset. Acceptable.

**Compliance Implications:**

GDPR Art. 32 (security of processing), Art. 5 (availability): users must retain the ability to access their own accounts even during a security incident. This ruling ensures password-recovery flow is part of the security defense, not an additional barrier.

**Audit Reference:**

Ruling issued during credential-stuffing incident response. Password-reset endpoint design and accessibility requirements must be met before account-lockout ships.
