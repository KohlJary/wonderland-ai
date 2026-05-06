## Ruling 003: Breach notification obligations — credential-stuffing success determination and user notification

**Severity:** critical
**Domain:** privacy
**Source:** Dormouse observation; attack includes successful logins (success rate dropped to 0.2%, but 0.2% of 4,127 is ~8 successful logins), implying credential compromise and unauthorized account access

**Citation:**

GDPR Art. 33–34 (breach notification); CCPA §1798.150 (consumer right to know); Most US state breach-notification laws require notification if credentials or authentication secrets are accessed or exfiltrated. The attack demonstrates credential compromise (attacker successfully logged in to accounts).

**Finding:**

The attack included successful logins. Dormouse telemetry shows success_count ≈ 8 accounts during the attack window. These accounts were accessed by the attacker without authorization. This is a data breach under GDPR/CCPA/state law definition. The users of these 8 accounts must be notified. Additionally, the attacker may have obtained credentials from an external breach list (common in credential-stuffing); those credentials may work on other systems; users should be advised to change passwords.

**Required Remediation:**

Identify the 8 user accounts with successful unauthorized logins during the attack window. For each: (1) log the unauthorized access with timestamp, attacker IP, session details; (2) immediately revoke all active sessions for that user; (3) queue a notification email to the user advising of unauthorized access, what was accessed (none, if attacker only logged in and did not access resources), and password-reset instructions; (4) flag account for manual review (support / security team) to determine if attacker accessed any user data; (5) prepare breach-notification filing if required by jurisdiction. The notification must be sent within 72 hours per GDPR; the filing must occur within the same window.

**Acceptance Criteria:**
- The 8 accounts with successful unauthorized logins are identified and logged
- All active sessions for those 8 accounts are revoked
- Notification emails sent to users, with: (a) timestamp of unauthorized access, (b) attacker IP, (c) instruction to change password, (d) notice of manual review in progress
- Breach-notification filing prepared (template in compliance artifact registry) and submitted to applicable regulator if required
- Audit trail complete: unauthorized access logs, session revocation logs, notification emails, filing receipt

**Residual Risk:**

Attacker may have exfiltrated user data during the 8 successful login sessions before being locked out. This is unknown. Dormouse must examine access logs for those sessions (what was queried, what was downloaded, did the user IP access unusual endpoints). If data exfiltration is confirmed, notification scope expands to all affected users and the breach is more serious.

**Compliance Implications:**

GDPR Art. 33–34 (notification timeline: 72 hours or 'without undue delay' to regulator, user notification must be 'in clear and plain language'); CCPA §1798.150 (right to know); Most US states require notification if credentials accessed; some require 'without unreasonable delay.' EU requires Art. 33 filing to DPA regardless of user notification decision; in most cases, user notification follows. Check jurisdiction for this system's users.

**Audit Reference:**

Unauthorized access logs for the 8 accounts; session revocation logs; notification email template and delivery logs; breach-notification filing and receipt from regulator; manual-review findings (separate artifact)
