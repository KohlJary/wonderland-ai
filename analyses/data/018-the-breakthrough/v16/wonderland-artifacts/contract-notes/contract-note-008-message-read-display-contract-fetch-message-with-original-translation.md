## Contract Note 008: Message read/display contract (fetch message with original + translation)

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

No explicit contract yet.

**Proposed Change:**

Backend exposes endpoint GET /api/messages/{message_id}. Response: { message_id (UUID), sender_id (UUID), original_text (string), original_language (enum), translated_text (string, nullable), target_language (enum, nullable), translation_status (enum: pending | complete | failed), translation_model (string, nullable), translation_timestamp (timestamp, nullable), message_retention_flag (string), created_at (timestamp) }. Frontend uses this to render the message. If translation_status=pending, frontend displays 'translating...' placeholder in translated_text lane. If translation_status=failed, frontend displays 'translation failed—retry?' with a retry button. Translation polling: frontend does NOT poll; assume translation completes before message is fetched (because message is only displayed after it is stored + translation is complete, or translation is visibly pending). Alternative (if translation is asynchronous): frontend can fetch the message and display it in pending state; a later fetch will show the completed translation. Clarify which model (sync vs async) is the contract.

**Source:** adr#1 and story#1-5: frontend must display original + translation together; translation_status tells frontend how to render incomplete state.

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

Backend query for GET /api/messages/{message_id} is O(1) lookup. Response includes translation_status so frontend can render UI appropriately. No transformation; return raw record. Invariant: response is consistent with the record stored—no post-hoc retranslation or data mutation.
