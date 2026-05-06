## Ticket 001: Backend: Message schema with translation state machine

**Sources:** story-001, story-002, story-003, adr-message-model-asymmetric-translation-with-state-machine-and-bidirectional-conversations, adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-002, ticket-003, ticket-004
- Blocked by: —
- Soft: —

**Description:**

Create Message table/model with fields: sender_id, receiver_id, conversation_id, original_text, translated_text, language_pair, translation_status (enum: pending_translation | translated | translation_failed), created_at, translated_at, error_code, error_message. Implement state machine: Message creation sets translation_status to pending_translation. Include validation that sender and receiver are both members of the conversation. No translation service calls in this ticket — just the schema and enum.

**Acceptance:**
- Message model persists with all required fields
- translation_status enum enforces the three valid states
- Message creation sets translation_status to pending_translation
- Conversation membership validation prevents cross-conversation messages
- Database migrations are applied and reversible

**Risk:**

If the ORM doesn't support enum types cleanly, fallback to string with check constraint — adds half a day.
