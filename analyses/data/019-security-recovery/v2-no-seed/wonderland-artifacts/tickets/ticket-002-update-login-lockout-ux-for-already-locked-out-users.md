## Ticket 002: Update /login lockout UX for already-locked-out users

**Sources:** dormouse-observation-credential-stuffing
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5–1 hour, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: rate-limit-middleware
- Soft: audit-logging

**Description:**

When a user hits the lockout threshold (either existing 5-failure threshold or Queen-refined value), return a specific error code/message on frontend. Frontend shows user-friendly lockout notice with recovery path (e.g., 'Account locked for 15 minutes; reset password to regain access'). Exact messaging and recovery path TBD by Queen ruling.

**Acceptance:**
- Frontend detects lockout response code and renders user-facing message
- Message includes estimated unlock time or recovery action
- No raw error codes leak to user; messaging is supportive, not alarming

**Risk:**

If the Queen rules that lockout duration or unlock mechanism changes, the UX may need iteration. Implement for the current behavior; fast-follow if ruling changes it.
