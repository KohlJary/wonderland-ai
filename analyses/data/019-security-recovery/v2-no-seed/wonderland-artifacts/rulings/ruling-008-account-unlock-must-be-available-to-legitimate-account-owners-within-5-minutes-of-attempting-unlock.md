## Ruling 008: Account unlock must be available to legitimate account owners within 5 minutes of attempting unlock

**Severity:** critical
**Domain:** authorization
**Source:** story from Alice: 'Affected user can regain access without waiting forever or jumping through chaos'

**Citation:**

CWE-640 Weak Password Recovery Mechanism for Forgotten Password (anti-pattern: recovery flow so friction-heavy it becomes inaccessible); OWASP Account Lockout & Proactive Denial of Service (principle: account recovery must be faster and easier than account takeover, or the lockout itself becomes a DoS against the legitimate user)

**Finding:**

Alice's story names the user need: regain access 'without waiting forever.' If the unlock flow takes 30 minutes (email arrives slowly, user misses the email, user does not realize unlock is an option), the 47 locked-out users escalate to support, creating a secondary incident (support queue overload) while the primary incident (the attack) is ongoing. The lockout is a necessary mitigation; the unlock flow is how the mitigation becomes user-defensible. Without fast unlock, the team is trading attacker damage for legitimate-user damage.

**Required Remediation:**

The unlock mechanism (email token, SMS code, security question, or combination) must complete in under 5 minutes from the time a locked-out user initiates unlock. This includes email delivery (configure MTA with SLA, or use SMS as primary). The unlock must not require user authentication beyond proof of account ownership (email access, SMS receipt, or answer to pre-set security question). The unlock must not require password re-entry as the unlock mechanism itself (password is compromised; re-entering it does not prove account ownership).

**Acceptance Criteria:**
- Email unlock-token delivery time is measured and confirmed under 3 minutes (99th percentile)
- SMS unlock-code delivery time is measured and confirmed under 2 minutes (if SMS is used)
- User initiates unlock → receives proof-of-ownership challenge → completes challenge → account is unlocked, all within 5 minutes wall-clock time
- Unlock mechanism is tested under attack conditions (Hatter scenario) to confirm it does not slow or degrade during incident
- Support team is trained on what unlock looks like so they do not create second-channel workarounds that bypass the flow

**Residual Risk:**

Email is asynchronous and can be delayed by MTA, ISP, spam filters. SMS is faster but costs money and has country-specific routing challenges. The Queen is accepting the risk that some users will experience >5 minute unlock time due to infrastructure delays, provided the unlock flow itself completes in <5 minutes and the Dormouse is monitoring for SLA breaches. If unlock SLA is breached more than 10% of the time, the flow must be redesigned to SMS-primary or security-question-primary (faster mechanisms).

**Compliance Implications:**

GDPR Art. 32 (security of processing) + Art. 33 (breach notification): a locked-out user unable to unlock within a reasonable time becomes a support escalation, which becomes a secondary vector for information leakage if support staff work around the flow. Fast, frictionless unlock for legitimate users reduces this risk.

**Audit Reference:**

Incident-response ruling: account-unlock timeliness SLA, locked-out user path, v1
