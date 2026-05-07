## Ticket 002: Add user-facing rate-limit messaging and error recovery

**Sources:** user-discovers-rate-limit-when-sending-rapid-messages
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-rate-limiting-enforcement-with-header-validation
- Soft: —

**Description:**

When the user hits a rate limit (receives 429), surface a clear message explaining the limit, when it resets, and what they can do. Include a countdown timer if Retry-After is present. Do not implement retry logic in the client — that's post-launch. Focus on making the limit visible and understandable so users don't spam the API in frustration.

**Acceptance:**
- 429 responses display a user-friendly error message with reset time
- Retry-After header is parsed and displayed as a countdown
- Message is distinguishable from other error types (5xx, auth errors, etc.)
- UX passes accessibility review (color, contrast, readability)

**Risk:**

Design review may slow this if messaging language is under-specified. Assume 1.5 days if copy requires multiple rounds.
