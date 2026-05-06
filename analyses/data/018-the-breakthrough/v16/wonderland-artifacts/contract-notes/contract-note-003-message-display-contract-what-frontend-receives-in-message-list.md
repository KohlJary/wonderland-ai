## Contract Note 003: Message display contract: what frontend receives in message list

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

Message GET endpoint returns { id, text, language_code, sender_id, timestamp, ... }

**Proposed Change:**

Message GET endpoint returns { id, original_text, original_language, translated_text (nullable), target_language (nullable), translation_status, translation_error (nullable), translation_model, translation_timestamp, sender_id, timestamp, ... }. If translation_status is 'pending' or 'failed', translated_text may be null. If translation_status is 'success', both original_text and translated_text are present. Message list endpoint (GET /messages) returns full shape for all messages in the thread.

**Source:** ticket-003, adr-001: UI must know translation_status to render correct state. Frontend needs translated_text and original_text together to render dual-display.

**Frontend Impact (Tweedledee):**

UI iterates message list and for each message renders: (if show_original) original_text + translated_text side-by-side, (if !show_original) translated_text only. Loading state: render spinner while translation_status='pending'. Error state: render original_text + error message + 'retry translation' button when translation_status='failed'. Client state: show_original toggle per-session, not persisted to server in v1.

**Backend Impact (Tweedledum):**

Backend query for GET /api/messages/{message_id} is O(1) lookup. Response includes full message record (original_text, translated_text, translation_status, etc.) so frontend can render appropriately. No transformation or post-hoc retranslation. Invariant: response is consistent with stored record. Message list endpoint GET /api/messages (with pagination/filtering) returns full shape for all messages in thread.
