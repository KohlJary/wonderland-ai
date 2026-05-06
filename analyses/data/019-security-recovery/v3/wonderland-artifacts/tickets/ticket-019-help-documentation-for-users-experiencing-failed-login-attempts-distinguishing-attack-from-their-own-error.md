## Ticket 019: Help documentation for users experiencing failed login attempts (distinguishing attack from their own error)

**Sources:** story: user-experiencing-the-attack-in-real-time-failed-login-attempts-from-their-own-location-device-needs-help-distinguishing-their-own-error-from-a-compromise
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: user-messaging-for-account-lockout-due-to-credential-stuffing-attack, ticket: user-messaging-for-rate-limiting-on-shared-ip-during-credential-stuffing-attack
- Soft: —

**Description:**

During the attack, users will experience failed login attempts in two scenarios: (1) they are trying to log in but hit the per-IP rate limit or per-email lockout (false positive from the user's perspective), and (2) they are trying to log in and genuinely forgot their password or mistyped it. Both groups will be confused about what went wrong. We must publish clear, accessible documentation that helps users self-diagnose: 'Is my account locked by the service (security), or is it my password (my error)?'. Success: user reads one page and understands whether they need to wait, reset password, or contact support. Failure: user doesn't know what to do and floods support with identical questions.

**Acceptance:**
- Documentation is published at a stable URL (e.g., /help/login-issues or support.example.com/login-failed-during-attack)
- Page explains the difference between 'account locked' (security), 'rate-limited' (temporary, shared IP), and 'wrong password' (user error)
- Page includes decision tree: 'Did you see a message about rate-limiting? If yes, wait 1 minute. Did you get a message about account lockout? If yes, reset your password. Otherwise, you may have mistyped your password.'
- Page includes links to password-reset, account-recovery, and support contact
- Page is written in plain language (not security jargon); tested with non-technical users for clarity
- Page is linked from the login page during the attack (visible to users who encounter errors)

**Risk:**

If documentation is hard to find or jargon-heavy, users won't read it and will contact support instead. If the decision tree is wrong or incomplete, users will follow the wrong recovery path and stay stuck.
