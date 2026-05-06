## Ruling 019: Breach-notification messaging must distinguish attack from user error

**Severity:** high
**Domain:** privacy
**Source:** story slug=user-experiencing-the-attack-in-real-time-failed-login-attempts-from-their-own-location-device-needs-help-distinguishing-their-own-error-from-a-compromise

**Citation:**

GDPR Art. 33-34 (personal data breach notification); NIST Cybersecurity Framework ID.AM-1 (Asset Management: understanding what data is at risk). When a user receives a breach notification, they must understand what happened, whether their own attempts or attacker attempts triggered it, and what action to take. Messaging that conflates user error with credential compromise creates false positives that erode user trust in legitimate security alerts.

**Finding:**

The Queen's ruling on breach-notification determination requires identifying which accounts had *successful* logins during the attack window. But users who experienced failed login attempts from their own device during the attack (because they mistyped their password, or because they were already locked out) will also see failed-attempt logs and may believe they are notified about a breach when the real breach is on a *different* account that was successfully compromised. This creates confusion and erodes the effectiveness of the notification.

**Required Remediation:**

Breach notifications must distinguish between (a) 'your account was successfully compromised and credentials were used' (high confidence, requires action) and (b) 'your account was targeted but not successfully accessed' (informational, monitor for suspicious activity). The notification must include specific details: which device/location made the successful login attempt (if successful), when it happened, and whether the user recognizes it. Users must be able to distinguish 'someone logged in as me' from 'someone tried and failed to log in as me.'

**Acceptance Criteria:**
- Breach notifications explicitly state whether the account was successfully compromised or only targeted
- If successful compromise: notification includes the device/IP/User-Agent used, the approximate time, and explicit instruction to change password immediately
- If only targeted: notification includes the number of failed attempts, the time window, and suggests monitoring for suspicious activity
- Notification includes a way for users to verify the login was not them (e.g., 'If you recognize this login, you can ignore this message')
- User testing confirms users understand what action is required for each notification type

**Residual Risk:**

Some users will still be confused; no messaging is perfect. Residual risk is mitigated by providing specific, verifiable details that allow users to distinguish their own behavior from attack behavior. This is acceptable.

**Compliance Implications:**

GDPR Art. 33-34: breach notifications must be clear and actionable. This ruling ensures notifications are not just sent, but are understood by recipients in a way that enables effective response.

**Audit Reference:**

Ruling issued during credential-stuffing incident response. Breach-notification messaging contract required before notification messages ship.
