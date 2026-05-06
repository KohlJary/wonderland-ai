## Ticket 016: User messaging for account lockout due to credential-stuffing attack

**Sources:** story: user-locked-out-by-credential-stuffing-attack-needs-to-know-why-and-how-to-recover
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-breach-notification-determination-which-accounts-succeeded-in-attack-per-queen-s-ruling
- Blocked by: ticket: implement-per-ip-rate-limiting-on-login-endpoint-per-queen-s-ruling, ticket: implement-account-lockout-policy-5-failures-user-notification-per-queen-s-ruling
- Soft: ticket: implement-rate-limit-and-lockout-observability-metrics-events-for-breach-notification-determination

**Description:**

When a user's account is locked due to failed login attempts (from any mix of IPs, during the credential-stuffing attack window), they receive a clear notification explaining: (1) their account has been temporarily locked due to suspicious activity, (2) this is a security measure protecting their account, (3) what they should do next: verify no unauthorized access occurred, reset their password, and regain access. The notification must distinguish between 'your password is wrong' (user error) and 'your account is locked for security' (attack response). Success: locked-out user can read one message and understand what happened and what to do. Failure: user is confused, contacts support, or assumes their account has been compromised and never returns.

**Acceptance:**
- User receives notification when account is locked due to failed login attempts
- Notification clearly states account is temporarily locked for security (not permanently compromised)
- Notification includes link to password-reset flow or account-recovery documentation
- Notification is sent via email to the registered account address, not in-app (so user can access it even if locked out)
- Message is tested with users who have actually been locked out (or close simulation) to confirm clarity

**Risk:**

If notification is unclear or delayed, users may not know how to recover; they may perceive the security response as a service failure. If the notification goes to the wrong email or doesn't arrive at all, the user has no path forward. Email delivery reliability must be confirmed before ship.
