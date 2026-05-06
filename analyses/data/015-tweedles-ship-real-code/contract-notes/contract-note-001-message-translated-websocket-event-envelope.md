## Contract Note 001: Message-Translated WebSocket Event Envelope

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Handler returns TranslationResponse {message_id, status, translated_text?, failure_reason?}. Frontend subscribes to message-translated events. Shape of the event payload: unspecified.

**Proposed Change:**

Formalize the WebSocket event envelope that the backend emits when a translation completes. Specifically: (a) Does the event payload include the full TranslationResponse, or just {message_id, status}? (b) Does it include the original message object, or only translation fields? (c) Does it include updated_at / translation_timestamp?

**Source:** Tweedledee frontend wiring — need the event shape to decide whether to cache from the event payload or use the event as a signal-to-refetch from the server.

**Frontend Impact (Tweedledee):**

Frontend cache rule: message-translated event carries {message_id, status, translated_text?, failure_reason?}. On arrival, frontend updates the cached message entry with translated_text (if status=translated) or caches failure_reason (if status=failed or timeout). No re-request; the event is authoritative. This assumes server persistence happens before event emission — i.e., GET /message/{message_id} after the event returns the same translation.

**Backend Impact (Tweedledum):**

Three constraints from my side:

**1. Payload shape: signal-only vs. full TranslationResponse**

The handler returns TranslationResponse {message_id, status, translated_text?, failure_reason?}. The WebSocket event needs to decide: does it include the full response, or just {message_id, status}?

Backend constraint: If the event includes translated_text, I avoid an extra fetch and emit one write-to-all-subscribers message per translation. That's cheaper on my side and simpler for the state machine. But it couples the event envelope to the full response forever — any future change to TranslationResponse shape requires versioning the event.

If the event is signal-only {message_id, status}, the frontend re-requests the full message and I have more HTTP load. But the coupling is loose: I can evolve TranslationResponse independently of the WebSocket event shape. I also avoid a subtle invariant violation: if the event includes translated_text and the frontend caches it directly, what happens if a third client edits the message after translation but before you've consumed the event? The translated_text becomes stale. A signal-only event forces you to re-request the authoritative state.

**My recommendation:** signal-only event {message_id, status}. The frontend re-requests the full message (cache-invalidation pattern). This costs an extra round-trip but keeps the invariant clean: the source of truth for the translated_text is the server, and every read confirms it.

**2. Original message object in the event?**

Backend constraint: No. The original message lives in a separate `messages` table; the translation lives in a `translations` table with a foreign key to `messages(message_id)`. Embedding the full message object in the WebSocket event creates redundancy and divergence risk. If the message is updated (e.g., edited by another client) after translation completes, the event carries stale message data. The frontend should re-request the message to get the current state.

**My recommendation:** the event carries only {message_id, status} (and failure_reason if status is failed/timeout). The frontend uses the event as a cache-invalidation signal and re-requests the full message via the message GET endpoint. This keeps the single source of truth at the server.

**3. Timestamp in the event?**

Backend constraint: If you cache from the event payload (i.e., my recommendation above is rejected and you do cache translated_text from the event), then yes, I need to include an updated_at or translation_timestamp. Without it, you can't detect if another client's edit raced your cache update.

If you accept the signal-only approach, the timestamp is not needed — the cache-invalidation pattern forces a re-request, and the GET endpoint returns the current message state with its current translation.

**My recommendation:** no timestamp in the signal-only event. The re-request gives you the current state with no ambiguity.

**Overall:** I'm proposing we ship the WebSocket event as {message_id, status, failure_reason?} and use it as a cache-invalidation signal rather than a full-payload event. The handler is already stateless; this keeps it stateless and avoids coupling the event envelope to response evolution. One extra round-trip on translation completion, but the invariant stays clean.
