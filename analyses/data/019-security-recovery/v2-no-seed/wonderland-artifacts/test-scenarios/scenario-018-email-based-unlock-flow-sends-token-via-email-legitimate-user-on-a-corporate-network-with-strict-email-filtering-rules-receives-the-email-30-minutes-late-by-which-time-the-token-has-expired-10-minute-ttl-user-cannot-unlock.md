## Scenario 018: Email-based unlock flow sends token via email, legitimate user on a corporate network with strict email-filtering rules receives the email 30 minutes late, by which time the token has expired (10-minute TTL), user cannot unlock

**Severity:** degradation

**Setup:**

User is rate-limited (shared corporate IP hits the threshold). User requests unlock and selects email as the recovery method. The unlock-send endpoint issues a token with a 10-minute TTL and sends email to user@company.com. The user's corporate email filters the email as potential phishing (recovery emails sometimes trigger filters). Email arrives in user's inbox 30 minutes later. User tries to unlock, but the token TTL has expired.

**Trigger:**

User submits the unlock form with an expired token, more than 10 minutes after the email was originally sent.

**Expected:**

Unlock endpoint rejects the expired token and offers a 'resend' option or clear guidance on next steps. User does not get a cryptic error. User does not have to wait for support or for the 5-minute lockout window to expire.

**Concern:**

Email delivery is not reliable on a 10-minute window. Corporate filters, ISP spam detection, email queue delays — all of these can push delivery past 10 minutes. If the token TTL is shorter than the p95 email delivery time, the unlock flow will fail for a fraction of users even when they do everything right. This is degradation, not breakage, because the user can still unlock (wait for the 5-minute lockout window to expire, or request a new token if the endpoint allows resends). But it adds friction and collateral lock-out time for users who did nothing wrong.

**Property:**

For all emails sent to a user with a recovery token, if the email is delivered within the corporate network's p95 delivery latency, the token must still be valid when the user opens it. Token TTL >= p95(email delivery time) for the user's email provider/network.

**Implies:**
- Implies observability concern for Dormouse: we need metrics on 'unlock token expired before user submitted it' to detect whether this is actually happening in production. If it is, the TTL needs to be extended or the resend flow needs to be more discoverable.
- Implies UX concern for Tweedledee: error messaging when a token expires must be extremely clear and actionable. 'Your unlock link has expired. Request a new one here.' Not 'Invalid token.' Not a cryptic error code.
