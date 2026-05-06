## Scenario 012: User requests unlock, email with token arrives, user clicks token link, token is already expired because the token TTL is shorter than the email delivery time

**Severity:** degradation

**Setup:**

The system implements email-based unlock with a 1-hour token TTL. User requests unlock. Email delivery SLA is not specified or is slower than expected (3 minutes in the happy path, but ISP queues, spam filters, and recipient mailserver delays can push it to 5-10 minutes). User receives the token, clicks the link, but the token has already expired (we issued it immediately at unlock request, 10 minutes ago; TTL was 1 hour, but system restarted and logs were not persisted, or the clock drifted, or the implementation uses wall-clock time instead of absolute time, and nobody validated the timing contract).

**Trigger:**

Email delivery takes 5-10 minutes (not 3 minutes); token TTL is 1 hour nominal but less in practice (clock skew, restart, etc). User clicks the link after email arrives.

**Expected:**

Token is still valid (issued 10 minutes ago, TTL 1 hour). User clicks link, account is unlocked. User logs back in.

**Concern:**

Email delivery is not instantaneous, and clock skew is real in distributed systems. If we set token TTL based on 'how fast email typically arrives' without margin, real users will experience token expiration. The feedback loop is harsh: user gets email (good), clicks link (good), sees 'invalid or expired token' (bad), re-requests unlock (friction), wait for email again (friction).

**Property:**

For all token requests, token_expiry > now + email_delivery_p99. (Email delivery is not under our control; we can measure the SLA and set TTL accordingly.)

**Implies:**
- Implies operational constraint on token TTL (Queen should rule acceptable email delivery SLA and we set TTL conservatively above it). This is not blocking but must be specified before the Tweedles implement unlock.
