## Contract Note 002: Translation Status Signal - Canonical Shape v2

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

TranslationResponse {message_id, status, translated_text?, failure_reason?} returned from handle_translation_request(). WebSocket event shape: unspecified.

**Proposed Change:**

Formalize the message-translated WebSocket event to include exactly: {message_id, status, translated_text?, failure_reason?}. Do not include the original message object in the event. The event carries only the translation result; cache reconciliation happens server-side (the canonical message object is already persisted; the event is the translation-complete signal).

**Source:** Frontend cache architecture. The frontend caches messages keyed by message_id. When a translation completes, the event should carry enough for the frontend to update its cache without a re-request. Including the full message object in the event duplicates the canonical state and creates reconciliation burden.

**Frontend Impact (Tweedledee):**

Frontend assumes message-translated event is authoritative. On status=translated, cache is updated from event payload without re-fetch. On status=failed or timeout, translation_status is updated and failure_reason is cached (for observability) but not shown to user. Cache consistency rule: frontend trusts that server persists translation before emitting event.

**Backend Impact (Tweedledum):**

[Tweedledum to fill in]
