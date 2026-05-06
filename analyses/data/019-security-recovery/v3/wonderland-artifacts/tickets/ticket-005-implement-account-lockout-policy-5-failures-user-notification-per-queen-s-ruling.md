## Ticket 005: Implement account lockout policy (5 failures + user notification) per Queen's ruling

**Sources:** ruling: account-lockout-policy-threshold-and-notification-adjustment, concern: white-rabbit-password-reset-flow-isolation-required-for-v1
**Owner:** Tweedledee & Tweedledum
**Tier:** v1
**Estimate:** 3-5 hours, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-breach-notification-determination-which-accounts-succeeded-in-attack
- Blocked by: ticket: confirm-password-reset-endpoint-scope-and-lockout-interaction
- Soft: —

**Description:**

Implement account-specific lockout after 5 failed login attempts on a single email address (per Queen ruling). When lockout triggers: (1) block further login attempts for that email for 30min (or Queen-specified duration); (2) send user notification (email or in-app) with unlock method (password reset or support contact). Modify User model to track lockout_until timestamp. Modify /auth/login endpoint to check lockout status before attempting auth. Coordinate with password-reset flow (see: blocking dependency) to ensure reset unblocks login.

**Acceptance:**
- Account locked out after 5 failed attempts on same email
- Lockout prevents further login attempts for 30min duration (or Queen-specified)
- User receives notification (email) on lockout with unlock method
- Password reset (or Queen-specified unlock method) clears lockout on that email
- Lockout_until field added to User model and tracked in migrations
- Tests cover: lockout triggering, lockout expiry, unlock via password reset

**Risk:**

Notification channel (email) may be compromised if attacker already has access to victim email (i.e., if they got past the account). Queen's ruling should clarify notification channel security posture. Assume email for now; escalate if unclear.
