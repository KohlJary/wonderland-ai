## Ruling 017: Account lockout notification must be authentic and actionable

**Severity:** high
**Domain:** privacy
**Source:** story slug=security-conscious-user-receives-lockout-notification-and-wants-to-verify-it-s-real-not-phishing

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; CWE-640 Weak Password Recovery Mechanism for Forgotten Password. Notifications about account security events are common phishing vectors; if the notification cannot be verified as authentic, attackers will use the legitimate lockout event as cover for account-takeover attempts.

**Finding:**

When a user receives a 'your account is locked' notification during the attack, they cannot distinguish a legitimate security alert from a phishing attempt designed to trick them into clicking a malicious reset link. This is a secondary attack surface: the attacker compromised credentials via stuffing, and now uses our legitimate lockout notification as social engineering. Users who do not trust the notification will click unverified recovery links in phishing emails, completing the account takeover.

**Required Remediation:**

Lockout notifications must be verifiable as authentic without requiring the user to click external links. The notification must (a) come from a channel the user has already verified as legitimate (e.g., the email address they registered with, sent via a domain they recognize), (b) include specific, non-guessable information that proves we have access to their account (not just their email address — e.g., the approximate time of failed attempts, the IPs or User-Agents involved), and (c) provide recovery instructions that do not require trusting an external link. A direct link to the password-reset flow within the application itself is acceptable; a link in email to an external domain is not.

**Acceptance Criteria:**
- Lockout notification is sent from a known, verified sender (noreply@[domain user registered with])
- Notification includes specific details about the failed attempt pattern (number of attempts, time window, source IPs or User-Agents) that only we could know
- Notification includes a copy-pastable recovery code or an explicit instruction to log in directly to [application domain] and use the password-reset flow within the app
- No notification includes an external link that could be phished
- User testing confirms users can distinguish the notification from phishing attempts

**Residual Risk:**

Determined attackers may still craft convincing phishing emails referencing the real lockout event. The residual risk is mitigated by (a) including non-guessable details that show we sent it, and (b) providing in-app recovery paths that do not require trusting email links. This is acceptable; perfect phishing resistance is unattainable.

**Compliance Implications:**

GDPR Art. 32 (security of processing): account-security notifications must be authentic and cannot themselves become vectors for account takeover. This ruling ensures notifications are part of the security defense, not a secondary attack surface.

**Audit Reference:**

Ruling issued during credential-stuffing incident response. Authentication-notification authenticity verification required before user-facing lockout notifications ship.
