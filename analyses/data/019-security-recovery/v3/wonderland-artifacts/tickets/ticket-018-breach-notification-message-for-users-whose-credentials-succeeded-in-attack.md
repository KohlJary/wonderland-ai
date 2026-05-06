## Ticket 018: Breach notification message for users whose credentials succeeded in attack

**Sources:** story: security-conscious-user-receives-lockout-notification-and-wants-to-verify-it-s-real-not-phishing
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: implement-breach-notification-determination-which-accounts-succeeded-in-attack-per-queen-s-ruling
- Soft: ticket: implement-rate-limit-and-lockout-observability-metrics-events-for-breach-notification-determination

**Description:**

For any user whose login credentials (email + password) were accepted during the credential-stuffing attack window, we must send a breach notification explaining: (1) their password was compromised (a malicious actor successfully logged in with it), (2) we have logged them out of all sessions and they must reset their password immediately, (3) they should check account activity for unauthorized changes, (4) they should rotate other passwords where they use the same email/password combination. The notification must be treated as high-priority and high-trust communication (not marketing email, not phishing-look-alike). Success: user receives notification, understands the severity, resets password, checks activity, moves on. Failure: user misses notification, doesn't reset password, attacker uses their session, and data is exfiltrated.

**Acceptance:**
- Breach notification is sent to all users whose credentials succeeded during the attack window (per breach-determination work)
- Notification is sent via email from a verified, recognizable account (not a noreply address)
- Email includes verifiable details (timestamp of unauthorized login, IP address of attacker, user's own IP address for comparison)
- Email includes direct link to password-reset flow (not a generic login page)
- Email includes phone number or support link for users who want to verify authenticity
- Notification is sent within 24 hours of breach determination (compliance requirement); cadence is documented
- Users who reset password are not required to re-login immediately (graceful recovery path)

**Risk:**

Breach notifications are high-trust communication; if they look like phishing or are unclear, users will ignore them or report them as spam. If notifications are delayed, attackers have more time to exploit the compromised sessions. If the password-reset link doesn't work or is confusing, users will be stuck without a recovery path.
