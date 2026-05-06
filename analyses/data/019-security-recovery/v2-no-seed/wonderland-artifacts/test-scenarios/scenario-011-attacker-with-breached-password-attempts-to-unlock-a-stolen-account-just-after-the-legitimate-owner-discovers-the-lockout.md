## Scenario 011: Attacker with breached password attempts to unlock a stolen account just after the legitimate owner discovers the lockout

**Severity:** breakage

**Setup:**

An attacker has credentials for user@example.com from a previous breach. The attack succeeds (0.2% = 8 successful logins during the credential-stuffing window per Dormouse observation). The attacker has a valid session. Meanwhile, the legitimate owner gets locked out after 5 failed attempts. The owner discovers the lockout, clicks 'Unlock', and the system sends them an email token. The attacker is also checking the inbox (if they have email access) or if the unlock mechanism accepts password, the attacker attempts unlock as well.

**Trigger:**

Both legitimate owner and attacker (who has the password and possibly the email) request account unlock at approximately the same time, in the same 5-minute window.

**Expected:**

The unlock mechanism validates account ownership via a factor the attacker does not have (email token that only the legitimate owner receives, security question answer the attacker does not know, or SMS OTP sent to the registered phone). The attacker's attempt fails because they lack this factor. The legitimate owner's attempt succeeds and the account unlocks.

**Concern:**

If the unlock mechanism accepts password as proof of ownership, the attacker (who has the password) can unlock the stolen account and maintain access. If the unlock mechanism validates via email token only, the attacker might still read the token email (if they have email access as part of a larger account compromise). The first case is a critical failure of unlock design; the second is a residual risk the Queen will accept explicitly. Without knowing which unlock primitive the Queen authorizes, I cannot verify this scenario.

**Property:**

For every unlocking session, there exists a proof-of-ownership credential that the attacker did not obtain from the leaked-credentials list. Unlock accepts that credential and rejects the breached password.

**Implies:**
- Implies architectural constraint on unlock authorization (Queen must rule which recovery primitive is acceptable). This blocks the Tweedles' unlock UX implementation.
- Implies that session audit trail must exist to distinguish legitimate sessions from attacker sessions (Cat's ADR-002 is critical path). Unlock revocation must invalidate breached sessions.
