## Ticket 004: Fetch messages in a conversation

**Sources:** story/conversation-is-persistent-and-both-users-see-the-full-history
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/create-messages-and-conversations-schema-add-send-message-endpoint
- Soft: —

**Description:**

Implement GET /conversations/{conversation_id} endpoint. Return all messages in the conversation in chronological order. Each message includes sender_id, sender_name, timestamp, original_text, translated_text, original_language, translated_language. Auth check: only users in the conversation can fetch.

**Acceptance:**
- GET /conversations/{conversation_id} returns 200 and a list of messages in chronological order
- Each message includes sender_id, sender display_name, timestamp, original_text, translated_text
- Only users in the conversation can fetch (auth check)
- Invalid conversation_id returns 404
- Non-member user returns 403

**Risk:**

Low. Straightforward query + auth check.
