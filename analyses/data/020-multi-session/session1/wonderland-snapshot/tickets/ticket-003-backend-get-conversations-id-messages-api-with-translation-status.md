## Ticket 003: Backend: GET /conversations/{id}/messages API with translation status

**Sources:** story-003, adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-005
- Blocked by: ticket-001
- Soft: —

**Description:**

Create API endpoint that returns all messages in a conversation with all fields, including translation_status, original_text, translated_text, and language_pair. Response format: [{ sender_id, original_text, translated_text, language_pair, translation_status, created_at, translated_at, error_code }, ...]. Include conversation membership check (caller must be one of the two users in the conversation). Support filtering by translation_status for audit queries (e.g., GET /conversations/{id}/messages?status=translation_failed).

**Acceptance:**
- Endpoint returns all messages with all required fields
- Membership check prevents non-participants from reading conversation
- translation_status filter works and is queryable
- Response includes both original_text and translated_text
- Endpoint latency is <100ms (cached or indexed on conversation_id)

**Risk:**

If conversation query is slow, add index on conversation_id. If audit filtering is used heavily, may need query optimization — plan for post-launch if needed.
