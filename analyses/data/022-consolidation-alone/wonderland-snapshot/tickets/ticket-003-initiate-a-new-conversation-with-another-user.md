## Ticket 003: Initiate a new conversation with another user

**Sources:** story/english-speaker-initiates-a-chat-with-a-german-speaker
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.5–1 day, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket/list-conversations-endpoint
- Blocked by: ticket/create-messages-and-conversations-schema-add-send-message-endpoint
- Soft: ticket/search-users-by-email-fast-follow

**Description:**

Implement POST /conversations (recipient_email) endpoint. Given a logged-in sender and a recipient email, create a row in conversations (or derive it if implicit pairs) and return the conversation object. Minimal error handling: recipient not found → 404, recipient is self → 400. This endpoint is the entry point for starting a new conversation.

**Acceptance:**
- POST /conversations with valid recipient_email creates a conversation and returns 201
- Conversation object includes conversation_id, user_a_id, user_b_id, created_at
- Calling POST /conversations twice with the same recipient returns the same conversation_id (idempotent)
- POST /conversations with non-existent recipient_email returns 404
- POST /conversations with self as recipient returns 400

**Risk:**

If the team chooses implicit conversation pairs, this ticket is trivial (just return a derived pair object). Confirm schema choice before starting.
