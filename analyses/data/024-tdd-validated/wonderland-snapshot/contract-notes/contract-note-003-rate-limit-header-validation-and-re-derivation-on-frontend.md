## Contract Note 003: Rate-limit header validation and re-derivation on frontend

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No prior contract.

**Proposed Change:**

Story 001 says response includes X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset headers (per ticket-001 acceptance). Frontend may display these in error state (e.g., 'X of Y requests remaining'). Ticket-001 acceptance says backend must reject spoofed headers and re-derive from server state. Frontend assumption: these headers in 429 response are authoritative; I will display them without client-side validation.

**Source:** ticket-001 acceptance + story-001 (user sees rate limit clearly)

**Frontend Impact (Tweedledee):**

Your schema question — JSON fields are integers (limit, remaining, reset_at as unix timestamp). Retry-After is the authoritative signal for countdown (preferred). You can display remaining/limit for user context (e.g., 'You've hit the limit of 10 requests per minute'), and use reset_at as a secondary countdown source if Retry-After is missing (fallback only). All three always present in 429 response.

**Backend Impact (Tweedledum):**

429 response includes fields in JSON body: limit (10), remaining (0), retry_after (seconds until reset). No separate reset_at unix timestamp field shipped in this version. Retry-After header is authoritative for countdown; JSON fields are mirrors of server state. Server rejects any X-RateLimit-* headers in request (they're ignored).
