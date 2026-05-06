## Implementation 001: Translation message handler with 2-second SLA fallback

**Side:** backend
**Ticket:** pending-rabbit-ticket
**Contract:** Translation Status Signal Shape v1 + Translation SLA Fallback Behavior v1 + WebSocket Statefulness v1. Response envelope: {message_id, status, translated_text | null, failure_reason | null}. Status enum: {pending, translated, failed, timeout}. Failure reason enum: {timeout, service_error, network_error}.
**Ready for review:** no

**Approach:**

Async handler taking message_id, source_lang, target_lang. Wraps the stub translator in asyncio.wait_for(timeout=2.0) to enforce SLA. Returns TranslationResponse TypedDict with status enum {pending, translated, failed, timeout} and either translated_text (on success) or failure_reason (on failure). Failure reasons: {timeout, service_error, network_error}. The handler is stateless — all context flows in the request; no cached state on the server.

**Invariants Enforced:**
- Every response includes message_id (string) — passed through from request.
- Every response includes status (enum {pending, translated, failed, timeout}) — set to one of the four values on all paths.
- translated_text and failure_reason are mutually exclusive — if status is 'translated', translated_text is non-null string and failure_reason is absent; if status is 'failed' or 'timeout', failure_reason is set and translated_text is null.
- On timeout, status is 'timeout' and failure_reason is 'timeout' (enforced by asyncio.wait_for timeout exception path).
- On success, status is 'translated' and translated_text is the result of the stub translator (non-null string).

**Schema Changes:**

None — this is a pure handler, no migrations. When message persistence lands, the schema will include a messages table with (message_id, source_lang, target_lang, source_text, created_at); the translation_status field will be computed server-side and pushed to clients via WebSocket. Persistence is deferred per the ADR.

**Failure Modes Handled:**
- Timeout (translator >2s): asyncio.wait_for raises asyncio.TimeoutError → caught, returns status='timeout', failure_reason='timeout'.
- Service error (translator service returns error): raises TranslationServiceError → caught, returns status='failed', failure_reason='service_error'.
- Network error (translator unreachable): raises TranslationNetworkError → caught, returns status='failed', failure_reason='network_error'.
- Unexpected error (unknown exception): caught as Exception, returns status='failed', failure_reason='service_error' as safe default. (In production, would be instrumented with logging.)

**Files:**
- src/translation_handler.py: async handler with timeout enforcement, response envelope typing, and stub translator

**Open Questions for Pair:**
- How does Tweedledee wire the message-translated WebSocket event emission when the handler returns? Does the event loop live on the handler side or does Tweedledee call handle_translation_request() from a WebSocket handler and emit from there?
- Client-side cache lifecycle: does Tweedledee cache by (message_id, source_lang, target_lang) tuple, or some other key? This affects whether the server needs to version cache-busting or signal when a translation has changed.
- On network_error or service_error, does Tweedledee show the original message to the user immediately, or does the client retry? We should document the retry boundary.

**Known Limitations:**
- Stub translator does not perform real translation — returns placeholder. Real integration requires third-party API client (medium severity — blocking for user testing).
- No instrumentation hooks yet — the exception handler catches and returns service_error for unknown exceptions. Dormouse will need metrics hooks (low severity — can land in v2).
- No message persistence yet — handler is stateless. Message storage and GDPR deletion surface are out of scope per the Cat's ADR (acknowledged — deferred).
- Client-side cache coherence semantics not yet specified. If a message's source text is edited after translation, we don't have a strategy for invalidating client caches (medium severity — may require contract note with Tweedledee).
