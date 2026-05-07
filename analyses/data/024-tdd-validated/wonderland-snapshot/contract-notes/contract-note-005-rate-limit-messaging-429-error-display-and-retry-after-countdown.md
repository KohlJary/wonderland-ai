## Contract Note 005: Rate-limit messaging: 429 error display and Retry-After countdown

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No user-facing rate-limit messaging yet.

**Proposed Change:**

When POST /api/messages returns 429, frontend parses response and displays user-friendly error: 'Rate limit exceeded. Try again in [countdown] seconds.' Countdown ticks down in real time if Retry-After is present. Message is visually distinct from 5xx, auth errors, and other error classes. UX is accessible (WCAG AA contrast, readable type, no color-only indicator).

**Source:** story-001 (user discovers rate limit), ticket-002 (user-facing messaging)

**Frontend Impact (Tweedledee):**

When 429 lands: user sees error state (distinct from network errors). Message renders Retry-After countdown (derived from response header). User cannot manually retry until countdown reaches zero. If user navigates away during rate-limit window, on return the countdown resumes from stored retry_available_at. Queued requests drain when window closes. Error state is recoverable (not a terminal error).

**Backend Impact (Tweedledum):**

No change from enforcement contract. Retry-After header is present in 429 response (already specified above). Response JSON may optionally include a human-readable reason field (e.g., 'rate_limit_exceeded') to help frontend distinguish this from other errors; I can add this if it helps your error handling.
