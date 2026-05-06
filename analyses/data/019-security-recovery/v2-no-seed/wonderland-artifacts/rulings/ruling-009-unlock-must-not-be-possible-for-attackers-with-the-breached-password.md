## Ruling 009: Unlock must not be possible for attackers with the breached password

**Severity:** critical
**Domain:** authorization
**Source:** the Cat's ADR on decoupling unlock authorization from authentication; the Queen's principle of separating what failed (password authentication) from how it is recovered

**Citation:**

CWE-640 Weak Password Recovery Mechanism for Forgotten Password (anti-pattern: recovery mechanism that re-uses the same credential that failed); OWASP Broken Authentication (principle: account recovery is a separate trust ceremony from login, and must not depend on the same credential that triggered the lockout)

**Finding:**

The 47 accounts are locked because too many attempts failed. But the Hatter's scenario #2 surfaces a harder case: what if some of the 4,127 attempted credentials *succeeded*? Those accounts are not locked, because the attacker authenticated successfully. The attacker then has a live session in a breached account. The legitimate owner is unaware. If the unlock mechanism accepts 'prove you own this account by entering the password' as sufficient, the attacker (who has the password) can also unlock any account they compromised. The unlock mechanism becomes a tool for the attacker to maintain access even if the legitimate owner later revokes the session.

**Required Remediation:**

The unlock mechanism must prove account ownership via a credential the attacker does not have. Email address (email access, not password), phone number (SMS receipt, not password), or pre-set security question (answer, not password) are acceptable. The unlock mechanism must explicitly *not* accept the password as proof of ownership. If a user has forgotten their password, that is a separate 'password reset' flow; 'account unlock' and 'password reset' must be distinct paths with distinct trust ceremonies.

**Acceptance Criteria:**
- Unlock flow branches: (1) if user knows password, unlock via email token, (2) if user doesn't know password, redirect to password reset flow (separate from unlock), (3) if user can answer pre-set security question, unlock via question answer
- Email token is time-bound (expires in 1 hour, non-reusable after first use)
- SMS code is time-bound (expires in 10 minutes) and single-use
- Security question answer does not require password and completes unlock immediately
- Test scenario (Hatter) confirms that attacker with breached password cannot unlock account, even if they know the email address

**Residual Risk:**

If the attacker has already exfiltrated the user's email account (part of a larger compromise), they can also unlock the account via email token. This is accepted as residual risk; the unlock mechanism is not responsible for detecting if the email account is also compromised. The Queen is accepting that this class of user (whose email is also compromised) will require support escalation and manual recovery.

**Compliance Implications:**

GDPR Art. 32 (security of processing): account recovery that does not re-use the failed credential demonstrates security-by-design and reduces the damage window if a credential is compromised. The Dormouse's audit trail will later show whether breached sessions accessed data; the unlock mechanism's separation from authentication reduces the risk that the attacker can hide their presence by locking the legitimate user out and then unlocking to maintain access.

**Audit Reference:**

Incident-response ruling: unlock mechanism must not re-use failed credential, v1
