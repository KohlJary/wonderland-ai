## Ticket 009: Implement user notification for breached accounts

**Sources:** ruling: breach-notification-obligations-credential-stuffing-success-determination-and-user-notification
**Owner:** Tweedledee & Tweedledum
**Tier:** v1
**Estimate:** 2-3 hours, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: implement-breach-notification-determination-which-accounts-succeeded-in-attack
- Soft: —

**Description:**

Notify users whose accounts were compromised in the credential-stuffing attack. Input: list of affected emails from Dormouse's breach-notification ticket. Output: send notification (email + in-app alert if available) to each affected user with: (1) statement that their password was used in a failed attack; (2) recommended action (change password immediately, enable MFA if available); (3) link to password-reset flow or support. Coordinate with Queen on notification template (legal/compliance review). Do not send breach notification to accounts with failed attempts but no successful logins (noise, not signal).

**Acceptance:**
- Notification template reviewed by Queen (compliance sign-off)
- Email sent to all affected users within 4 hours of breach determination
- Notification includes: breach statement, recommended action, password-reset link
- In-app alert (if available) shown on login/dashboard for affected users
- Notification log recorded (for compliance audit trail)

**Risk:**

Notification template must be legally reviewed by Queen before shipping. Do not send without her approval.
