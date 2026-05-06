## Ticket 003: Message model with translation surface (storage + on-read contract)

**Sources:** adr: user-language-capability-model-message-translation-surface, story: user-receives-a-message-from-someone-speaking-a-language-they-don-t-speak
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 1-2 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: translation-service-integration-and-vendor-contract, message-send-and-receive-api-endpoints
- Blocked by: conversation-model-with-language-pair
- Soft: —

**Description:**

Define Message(id, conversation_id, sender_id, text_original, text_language, created_at, deleted_at). Translation results are NOT stored in message table; instead, the Message.GET endpoint accepts ?read_language parameter and calls translation service on-read. Return both original and translated text to frontend for transparency (per Sophie's confusion-flag). Caching translation results is fast-follow. Include soft-delete for GDPR.

**Acceptance:**
- Message table schema matches ADR (id, conversation_id, sender_id, text_original, text_language, created_at, deleted_at)
- soft-delete works (WHERE deleted_at IS NULL filters active messages)
- Draft GET endpoint signature defined: GET /conversations/{id}/messages?read_language=de returns [{id, text_original, text_language, sender_id, created_at, text_translated}]
- Translation call contract specified (what data flows to vendor, error handling, retry logic)

**Risk:**

Translation service latency on read could make chat feel slow. Estimate assumes synchronous call; if latency > 500ms observed later, async caching becomes v1 (expand estimate to 2–3 days). Also: vendor data flow must pass Queen's review before implementation.
