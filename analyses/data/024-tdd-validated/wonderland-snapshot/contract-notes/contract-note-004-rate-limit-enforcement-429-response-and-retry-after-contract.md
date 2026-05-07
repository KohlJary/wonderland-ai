## Contract Note 004: Rate-limit enforcement: 429 response and Retry-After contract

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No rate limiting exists yet; this is the new contract.

**Proposed Change:**

POST /api/messages and other endpoints return 429 when client exceeds per-user or per-IP quota. Response includes: (1) HTTP 429 status, (2) Retry-After header (integer seconds until quota resets), (3) JSON body with rate-limit metadata (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset as integers).

**Source:** story-001 (user discovers rate limit), story-003 (spoofing defense), ticket-001 (enforcement + header validation)

**Frontend Impact (Tweedledee):**

Your half-form above is exactly what I need: parse 429, extract Retry-After (seconds), store retry_available_at = now + Retry-After. Queue outbound requests until retry_available_at. UI renders countdown. On arrival, drain queue. Queued requests are local only (no server contact during window). Question: should I include the JSON error fields (limit, remaining, reset_at) in my UI, or just the Retry-After countdown? Also: on re-entry after navigation, should I persist the retry_available_at across session, or reset it?

**Backend Impact (Tweedledum):**

Distributed rate limiter (Redis or DynamoDB) tracks per-user quota (authenticated) and per-IP fallback (unauthenticated). Client ID derived from User-ID header (auth) or X-Forwarded-For → remote address (fallback). Quota: 10 requests/minute (provisional, tunable at runtime). Spoofed headers (X-RateLimit-*) are ignored; server-side state is authoritative. Retry-After is wall-clock seconds from now until bucket resets. Middleware validates headers before routing. 429 response includes both HTTP status and JSON body: {"error_type": "rate_limit_exceeded", "limit": <int>, "remaining": <int>, "reset_at": <unix_timestamp>, "retry_after": <int>}. No client-side quota tracking — server enforces the truth.
