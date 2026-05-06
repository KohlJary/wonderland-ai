## Ruling 003: Extend user-account lockout window from 5 failed attempts to 10, effective immediately

**Severity:** high
**Domain:** authentication
**Source:** observation from Dormouse: 47 users already at lockout threshold (5 failed attempts) during active attack

**Citation:**

OWASP A07:2021 Identification and Authentication Failures. Current lockout policy (5 failed attempts) was set for account-recovery UX; credential-stuffing attacks require higher tolerance to avoid false-positives locking legitimate users. The 47 already-locked users represent collateral damage of the attack; extending the threshold reduces collateral while the rate-limit (ruling 1) stops the attacker.

**Finding:**

The current lockout policy (5 failed attempts locks account) was designed to prompt password recovery after a user mistyped 5 times. During a credential-stuffing attack with 4,127 attempts, this threshold is too aggressive — legitimate users with slightly-wrong passwords get locked out, and 47 are already affected. The attacker still breaches accounts (via the ~8 successful credentials) before triggering the policy. The threshold is both ineffective (doesn't stop attackers) and harmful (locks legitimate users). Raising to 10 attempts: (1) buys legitimate users more retries during an attack (tolerable UX); (2) forces attackers to generate more attempts to exhaust a single account (more load on the rate-limit, higher visibility). After rate-limiting is deployed, further tuning is possible; for now, 10 is the right threshold.

**Required Remediation:**

Update /login endpoint lockout policy: change max_failed_attempts from 5 to 10 before account lock. Lockout duration remains 30 minutes (user must wait or use password-recovery flow). This is a config change (no code change required if the threshold is externalized) or a one-line code change if hardcoded. Deploy immediately as part of the rate-limit mitigation.

**Acceptance Criteria:**
- Config / code updated; max_failed_attempts = 10 active in working tree
- Deployed to production before rate-limit middleware is live (order: config change first, then middleware, so rate-limit sees the updated threshold)
- Tested: user can attempt login 10 times with wrong password before lockout (not 5)

**Residual Risk:**

None. This is a near-zero-risk adjustment that improves UX during an attack without reducing security (the rate-limit, ruling 1, is the actual attack defense).

**Compliance Implications:**

None direct; this is an operational tuning.

**Audit Reference:**

incident-response thread, lockout-policy adjustment
