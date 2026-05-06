## Ticket 006: Add 'Unlock Account' CTA to login page for locked-out users who know their credentials

**Sources:** story:user-locked-out-can-unlock-without-support-friction-if-they-own-the-account
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket:implement-account-unlock-workflow-for-rate-limited-users
- Soft: —

**Description:**

Users who know their username/password but are locked out need a way to request an unlock without re-attempting login (which would just trigger the rate-limit again). Add a secondary CTA on the login page: 'Locked out? Unlock your account.' Clicking it opens a minimal form asking for username/email, triggers the unlock workflow from ticket:implement-account-unlock-workflow-for-rate-limited-users, and displays confirmation.

This removes friction: the user doesn't have to interpret the error message, find a support link, or wait for a fixed timeout. They see the button, click it, check their email.

**Acceptance:**
- Login page displays 'Locked out? Unlock your account' CTA below the password field
- CTA is visually distinct from primary login button but not intrusive
- Clicking opens a form asking for username or email
- Form submission triggers the unlock workflow (sends email with token)
- Confirmation message displays: 'Check your email for unlock link'
- Link text is clear and actionable (Alice's standard)

**Risk:**

Low. This is purely frontend, depends on the unlock workflow being shipped, and is a low-complexity addition. Could ship even if the unlock workflow has rough edges — the form just triggers it.
