## Scenario 010: An attacker with the breached-credentials list attempts to unlock a stolen account using the same email recovery mechanism that legitimate users use, timing the unlock to be just after the account is locked out

**Severity:** curiosity

**Setup:**

Attacker has username+password for account X (from the breached list). They attempt login at T=0, get rate-limited, and see 'account locked' error at T=1. At T=2, they receive the account-owner's unlock email (intended for the legitimate owner, sent via a side channel we don't control — the attacker is watching the legitimate owner's email or the email forward is compromised). At T=3, the attacker clicks the token link and completes the unlock flow. At T=4, they log in with the original password and are now past the lockout. This is a failure of the unlock mechanism to re-authenticate the account-owner — the token is not bound to a human, just to an account ID.

**Trigger:**

Attacker completes unlock flow without proving they own the account; unlocks are open to anyone with the unlock token.

**Expected:**

The unlock token should be bound to the account-owner's identity (email, phone, recovery code) — it should not be sufficient to click the link and be unlocked. The token should require the user to prove ownership: entering the account password, answering a security question, or confirming via another channel.

**Concern:**

This is a delightful gotcha: the unlock mechanism is more permissive than the lockout mechanism it is trying to bypass. If the attacker has the email, they also have the password, so re-requiring the password on unlock seems redundant — but it's actually the only proof that the person unlocking is the account-owner, not just someone who read the unlock email. The token-only unlock trades account-recovery friction for account-takeover risk. This scenario is unlikely in practice (requires attacker to intercept unlock email), but it is a real seam in the threat model.

**Property:**

For all unlock tokens T issued for account A, redeeming T to complete unlock of A must require proof-of-ownership of A beyond possession of T. This proof can be password, security question, or out-of-band confirmation, but token alone is insufficient.

**Implies:**
- Implies threat-model decision: is the unlock flow required to re-authenticate, or is possessing the token considered proof of ownership? Queen's ruling may need clarification here — this is a security design choice, not a bug. Flag for Queen.
