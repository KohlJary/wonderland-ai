## Scenario 006: User enters correct unlock email, clicks token link, token is already expired because we issued it too early in the flow

**Severity:** breakage

**Setup:**

User is locked out, receives unlock email with token immediately (within 30 seconds of unlock request). They click the link 8 minutes later—the token has a 5-minute validity window. They submit the form expecting unlock but receive 'token expired.' They request a new unlock email but the rate-limit on email-send (to prevent unlock-email-flooding) denies them for another 2 minutes. They are now locked out *and* cannot request unlock.

**Trigger:**

User clicks valid token link after expiration window has passed; token is no longer in the database.

**Expected:**

System should either: (a) return 'token expired, request a new one' with a frictionless 'send new email' button, or (b) extend the validity window to match user-realistic time-to-click (10-15 minutes). Not a hard block.

**Concern:**

The unlock token validity window is probably inherited from a password-reset flow designed for 'user checks email immediately.' But 'locked out user panic-checking email on mobile' has a much wider distribution. If the window is tight, we trade solving the attack for creating a separate unlock-failure class.

**Property:**

For all unlock tokens T issued at time I, the validity window must be wide enough that 95% of legitimate users clicking the link fall within the window. The window should degrade gracefully to 'send new email' rather than hard-block.

**Implies:**
- Implies UX decision: unlock email needs a prominent 'send new email' CTA visible even on expired-token error — flag for Tweedledee.
- Implies token validity window is a load-bearing constant — must be tuned by the Dormouse's observation of 'time from email send to user click' distribution in production.
