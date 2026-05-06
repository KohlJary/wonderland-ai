## Contract Note 003: Translation error handling and latency contract

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

When translation service is unavailable (timeout, rate limit, invalid key, vendor down), backend returns message with text_translated=null and translation_status=error_original_returned. Frontend MUST display original text (text_original) and a warning badge to user: 'Translation unavailable—showing original'. No silent fallback to original (user must know translation failed). Latency SLA: target <500ms per message; if observed >500ms, fast-follow implements server-side caching (Translation table). Retry logic: backend retries vendor once on transient errors (timeout); permanent errors (invalid key) bubble to frontend as error_original_returned.

**Source:** ticket-003 (failure mode handling) + ticket-004 (vendor integration)

**Frontend Impact (Tweedledee):**

I render translation_status=error_original_returned by showing a warning badge: "Translation unavailable—showing original" next to the original text. No silent fallback (I always show the original when translation fails, and I always show the warning). User can retry by refreshing the message list; backend retries vendor once per refresh. I do NOT implement client-side retry logic. If the user wants retries beyond that, it's a future feature (e.g., manual "retry translation" button). Open question: should the error badge be dismissible, or should it stay visible? Proposing: error badge is dismissible (user clicks to hide) but the original text remains visible. This respects the transparency requirement (user knows translation was attempted) while not being noisy.

**Backend Impact (Tweedledum):**

Translation client implements retry (max 1 retry on transient error). Timeouts set to <300ms to leave <200ms for response marshaling. Permanent errors caught and converted to error_original_returned status. No silent failures.
