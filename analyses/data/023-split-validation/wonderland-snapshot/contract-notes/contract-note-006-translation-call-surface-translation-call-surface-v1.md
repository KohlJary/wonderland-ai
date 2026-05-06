## Contract Note 006: Translation call surface (translation-call-surface-v1)

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

not yet defined

**Proposed Change:**

When receiver requests GET /conversations/{id}/messages?read_language=de, backend calls translation vendor for each message where sender's language != read_language. Call happens synchronously (frontend waits for response). On success: returns text_translated field populated. On vendor error (timeout > 5s, auth failure, rate limit): returns text_translated empty, translation_status='error', translation_error with user-facing message. Frontend shows warning: 'Translation unavailable; showing original text.' Retry logic: backend retries once on timeout, then returns error. No client-side retry needed. No conversation history sent to vendor (just current message text); ticket 004 confirms this.

**Source:** ticket 003 risk: 'Translation service latency on read could make chat feel slow'; ticket 004 acceptance: 'Vendor error returns original text + frontend-visible warning'

**Frontend Impact (Tweedledee):**

I need to handle translation_status='error' + display translation_error message to user. I'm not implementing retry logic on the client; I trust backend's one retry. If the user wants to retry, they refresh the message list and the backend tries again. This is acceptable for v1 (Akira's confusion-flag doesn't require instant retries). Open question: should I show the translation_error verbatim to the user, or should I show a generic 'Translation unavailable' message and log the error for debugging? I'm proposing generic user message + log the error_detail for support.

**Backend Impact (Tweedledum):**

My side mirrors yours: synchronous vendor call on GET, one retry on transient error, permanent errors converted to error_original_returned. Timeouts set to 300ms (your target <500ms per message is achievable). On vendor error, I return text_translated=null, translation_status='error_original_returned', translation_error='{vendor_error_detail}'. You proposed generic user message + log for support; I agree. I'll structure the error_detail as a private field (not shown to user) and return a public translation_error message (e.g., 'Translation service unavailable') to the frontend. Regarding conversation history: ruling-003 confirms NO context sent to vendor (MVP scope). I'll only send current message text to vendor, not conversation history. Future feature ticket for context-aware translation can reassess this. One backend-specific detail: vendor integration happens in a translation_worker service (separate from the message service). If the worker is down, the message service gracefully returns error_original_returned (no cascading failure). This requires a health check or circuit breaker. Fast-follow: implement retry caching so repeated reads of the same message don't re-call vendor; current design accepts latency hit on first read.
