## Ruling 007: Locked-out users must receive clear, actionable error messaging immediately

**Severity:** critical
**Domain:** data-handling
**Source:** story from Alice: 'Locked-out user sees clear, actionable error and knows what to do'

**Citation:**

OWASP A04:2021 Insecure Design (section: user-facing error surfaces must not leak attack information but must empower legitimate users); CWE-209 Information Exposure Through an Error Message (anti-pattern: generic error 'try again later' vs specific error 'too many failed attempts, unlock via email')

**Finding:**

The rate-limit enforcement (Tweedledum's implementation) will return HTTP 429 or account-locked status to 47+ users in the next 10 minutes. If the error message is generic ('An error occurred') or vague ('Try again later'), legitimate locked-out users will not understand they are locked out, will not know unlock is possible, will not know how to regain access, and will escalate to support (cost to team) or abandon the account (cost to user retention). The error surface is the first touchpoint in the unlock journey; it must be specific without leaking information the attacker would find useful.

**Required Remediation:**

Error response to rate-limited and locked-out login attempts must communicate three things clearly: (1) the account is temporarily locked due to too many failed attempts, (2) this is a security measure to protect the account, (3) the user can unlock by [specific mechanism — email link, SMS code, or security question answer, per the Cat's ADR and the unlock-flow implementation]. The error must not reveal whether the account exists, whether the username is recognized, or any other information that refines an attacker's guessing strategy.

**Acceptance Criteria:**
- Rate-limited response (HTTP 429) displays: 'Too many login attempts from this network. Please try again in [N] minutes, or unlock your account via email.'
- Account-locked response displays: 'This account is temporarily locked due to too many failed login attempts. Unlock it immediately via email, or contact support.'
- Error surface does not leak username existence, password validity, or any other discriminator
- Error surface is tested (Hatter scenario) to confirm it does not confuse legitimate users or provide attack-useful information
- Frontend renders the error message in a place the user cannot miss (not a toast, not a footnote)

**Residual Risk:**

If the unlock mechanism is not ready when this error ships (e.g., email-token flow is not implemented yet), users will receive clear direction to an unlock path that does not exist. This is worse than a vague error because it promises a solution and fails to deliver. The error message must ship in lockstep with the unlock mechanism, or not ship at all.

**Compliance Implications:**

GDPR Art. 32 (security of processing): user-friendly error messages that empower legitimate users to regain access reduce support escalations and incident response friction, demonstrating security-by-design. Generic error messages increase user frustration and support load, which increases risk of information leakage during support interactions.

**Audit Reference:**

Incident-response ruling: error messaging surface, locked-out user path, v1
