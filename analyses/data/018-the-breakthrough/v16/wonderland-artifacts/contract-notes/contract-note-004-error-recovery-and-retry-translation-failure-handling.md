## Contract Note 004: Error recovery and retry: translation failure handling

**State:** agreed
**Contract Version:** v1 (frontend-owned retry via /translate; backend-owned PUT for message update)

**Current Shape:**

No error handling for translation in current message flow.

**Proposed Change:**

When translate service fails (ticket-002), message is stored with translation_status='failed' and translation_error populated (e.g., 'unsupported_language_pair: EN->ZH', 'timeout: no response in 10s'). Frontend renders error state with 'Retry' button. User clicking 'Retry' calls /translate again with same (original_text, original_language, target_language) and updates message with result. Retry is idempotent: calling /translate on a message that already has translation_status='success' is no-op (or 400).

**Source:** ticket-004 acceptance criteria: sad path (translate fails) must degrade gracefully. UI must not crash; message must be readable in original language.

**Frontend Impact (Tweedledee):**

Frontend caches successful translations and retries saves using the cache. Re-requests translation only if /translate itself fails or times out. If save fails, retry save with cached translation. Clean rule, no hidden timeouts.

**Backend Impact (Tweedledum):**

On translation retry, frontend calls /translate again with same (original_text, original_language, target_language). Backend returns new translation (non-idempotent at model level, but idempotent at API level: same inputs yield consistent outputs). Frontend updates message via PUT /api/messages/{message_id} with new translated_text + translation_status. Backend enforces: original_text + original_language are immutable; only translated_text, translation_status, translation_timestamp can be updated. Retry is auditable via translation_model + translation_timestamp (multiple timestamps indicate retries).

**Resolution:**

Agreed. Error path finalized. Frontend retries /translate on failure; backend updates message via PUT /api/messages/{message_id} with new translated_text + translation_status. Translation_status transitions immutable (pending → complete|failed, no revert).
