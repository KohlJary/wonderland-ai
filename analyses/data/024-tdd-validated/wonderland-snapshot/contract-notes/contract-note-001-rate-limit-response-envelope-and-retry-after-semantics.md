## Contract Note 001: Rate-limit response envelope and Retry-After semantics

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No prior contract; green field.

**Proposed Change:**

When a request exceeds rate limit quota, backend returns 429 with structured response body and Retry-After header. Frontend parses Retry-After to display countdown timer to user (ticket-002).

**Source:** ticket-002 (user-facing messaging) + ticket-001 (enforcement)

**Frontend Impact (Tweedledee):**

Frontend needs to parse 429 response and extract: (1) Retry-After header (integer seconds), (2) error message body to display to user. I need to know the JSON shape of the error response so I can reliably extract user-friendly text. Story 001 accepts that 429 response is 'human-readable' — backend owns the clarity of that message, but I need to know what field(s) I'm reading from. Also need to confirm: does 429 return a JSON body at all, or just headers + status code?

**Backend Impact (Tweedledum):**

429 response body is always JSON with fields: error (string 'rate_limit_exceeded'), reason (human-readable message), limit (int quota), remaining (int 0), retry_after (int seconds until reset). Retry-After header is the same int in seconds. Frontend reliably parses by reading 'reason' or 'error' field + 'retry-after' header.
