## Ruling 004: Post-incident credential rotation — all authentication secrets in scope

**Severity:** high
**Domain:** secret-handling
**Source:** Credential-stuffing attack implies attacker has active credentials or session tokens for at least 8 accounts

**Citation:**

CWE-522 Insufficiently Protected Credentials; Industry best practice post-breach: assume attacker has credential material; rotate all secrets that may have been compromised. For credential-stuffing attacks, the attacker obtained credentials from external breach; those credentials may remain valid in the target system.

**Finding:**

The 8 successful logins mean the attacker had valid credentials for those accounts. These credentials remain valid unless reset. The attacker may still have them; they may have exfiltrated them to a marketplace. Any account whose credentials were used in a failed attempt should also be considered at risk (the attacker has the username-password pair; they simply didn't enter it successfully during the attack window, either by luck of iteration order or because the password has since changed).

**Required Remediation:**

All user passwords that were targeted in the attack (whether successful or failed) must be reset. This includes: (1) the 8 accounts with successful logins (mandatory); (2) the 2,795 accounts with failed attempts (force-reset on next login). Additionally, if the system uses API tokens or session tokens for programmatic access, and if any of those tokens were exposed, rotate them immediately. Service-account credentials, database passwords, third-party API keys — audit what secrets exist in scope and whether any could have been exfiltrated.

**Acceptance Criteria:**
- The 8 accounts with successful logins have passwords reset (forced)
- The 2,795 accounts with failed attempts are flagged to require password reset on next login
- Dormouse confirms: no logins from these accounts using old credentials occur post-deployment
- Audit trail: password-reset events logged with user_id, reset_method (admin-forced vs. self-initiated), timestamp
- All service-account credentials and API keys in scope have been audited; any with potential exposure have been rotated

**Residual Risk:**

Users will face forced password resets, which may generate support tickets and friction. Acceptable cost of incident response.

**Compliance Implications:**

Password reset is part of incident response and must be documented for breach-notification filing.

**Audit Reference:**

Password-reset logs; service-account credential-rotation logs; incident-response documentation
