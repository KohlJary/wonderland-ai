## Scenario 013: Legitimate user on a shared corporate network IP is collateral-locked; support is unreachable; self-service unlock requires account email but user cannot access email from the locked network due to proxy/firewall rules

**Severity:** degradation

**Setup:**

A user works in a corporate office that shares a network IP range. During the attack, one attacker request comes from the same IP pool (possibly routed through the same exit router, or the office has a larger IP block and the attacker happened to target from within it). The office's firewall blocks external email access for security reasons. The user is locked out. The self-service unlock flow sends a token to their registered email. But the user cannot access their email from inside the office network due to firewall rules. Support is swamped with incident-response questions and has a 2-hour wait queue.

**Trigger:**

Legitimate user attempts unlock via email token. User is on a network with no outbound email access. User cannot receive the unlock email, or receives it but cannot click the link to validate.

**Expected:**

The user should have an alternative unlock path (SMS OTP, security question, or support escalation that does not have a 2-hour wait queue).

**Concern:**

Email-only unlock is fragile if the user cannot access email from their physical location. The secondary unlock path must be specified before we ship email-only unlock to production. If we ship email-only without a fallback, users in this situation are stuck until support is available.

**Property:**

For all users in the locked-out cohort, at least one out of {email unlock, SMS unlock, security question unlock, or support escalation with SLA < 1 hour} is available.

**Implies:**
- Implies operational constraint on unlock fallback paths (Queen should rule whether SMS or security questions are acceptable, and what support SLA is acceptable). Tweedles cannot ship email-only unlock without a fallback.
