## Ticket 006: Confirm /password-reset endpoint scope and lockout interaction

**Sources:** concern: white-rabbit-password-reset-flow-isolation-required-for-v1
**Owner:** Tweedledee & Tweedledum
**Tier:** v1
**Estimate:** 0.5-1 hour, 90% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-account-lockout-policy-and-user-notification
- Blocked by: —
- Soft: —

**Description:**

Read src/auth/endpoints.py and check whether POST /auth/password-reset exists. If it does NOT exist: document this as a dependency for account-lockout v1 (password reset is the unlock method; if it doesn't exist, lockout has no escape hatch except time). If it DOES exist: confirm that password-reset rate-limiting is separate from /login rate-limiting (Hatter's scenario flagged this) and that /password-reset is not itself rate-limited in a way that locks out already-locked users. If interaction is broken, surface as a blocking dependency for account-lockout ticket.

**Acceptance:**
- Confirmation: /password-reset endpoint exists or does not exist
- If exists: rate-limit policy is separate from /login rate-limit (no cross-contamination)
- If exists: password-reset flow successfully unblocks an account in lockout state
- If does not exist: documented as dependency blocker with clear scope

**Risk:**

Low. This is a read-only confirmation ticket. Risk is only if the confirmation surfaces a breaking issue with password-reset; in that case, ticket the fix immediately.
