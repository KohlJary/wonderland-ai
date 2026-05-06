## Ruling 009: Password-reset endpoint rate-limiting — must not lockout legitimate password-recovery flow

**Severity:** high
**Domain:** authentication
**Source:** test_scenario from Hatter: 'lockout-escape-hatch-legitimate-password-reset-flow-must-not-be-rate-limited'

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; NIST SP 800-63B §5.1.4.2 on account recovery mechanisms. If account lockout prevents password reset, users cannot self-recover, and the password-reset endpoint becomes a secondary attack vector for account takeover.

**Finding:**

If the /password-reset endpoint shares rate-limiting policy with /login, a user locked out by credential-stuffing cannot reset their password to regain access — the reset flow is also rate-limited. Additionally, an attacker can spam the reset endpoint to lock users out of password recovery, ensuring account takeover. This creates a compounding failure where lockout (a security control) becomes a denial-of-service vector.

**Required Remediation:**

The /password-reset endpoint must have a *separate* rate-limiting policy from /login, and must be designed to prevent lockout from blocking password recovery. Recommended approach: /password-reset allows N attempts per email per hour (N ≥ 5, to allow legitimate typos and retries), independent of /login rate-limiting. This allows users to escape lockout via password reset while still defending against reset-spam attacks.

**Acceptance Criteria:**
- Code inspection confirms /password-reset and /login have distinct rate-limit policies
- Hatter's scenario 'lockout-escape-hatch-legitimate-password-reset-flow-must-not-be-rate-limited' passes: a user locked out by /login rate-limiting can still successfully submit a password-reset request
- Hatter's scenario implicit corollary passes: spamming the /password-reset endpoint does not prevent the legitimate password holder from using the reset flow

**Residual Risk:**

A user can reset their password to recover from lockout, but they will not receive the reset email until the rate-limit window clears on /login — i.e., the recovery path works but may be slow. This is acceptable; it prevents immediate account takeover while still allowing recovery.

**Compliance Implications:**

GDPR Art. 32 (security of processing) + account recovery obligation: users must be able to regain access to their accounts through a recovery mechanism even if they are locked out. If lockout prevents recovery, the system does not meet the recovery requirement.

**Audit Reference:**

Threat Garden entry: 'Password-reset flow as secondary attack vector during credential-stuffing incident'; ruling issued in response to scenario discovery; must be implemented before v1 ship.
