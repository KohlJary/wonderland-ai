## Ticket 002: Create messages and conversations schema; add send-message endpoint

**Sources:** story/english-speaker-initiates-a-chat-with-a-german-speaker, adr/message-routing-and-user-identity-for-peer-to-peer-translation-chat
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1.5–2.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: ticket/fetch-conversation-messages-endpoint, ticket/list-conversations-endpoint
- Blocked by: ticket/set-up-http-basic-auth-signup-login-endpoints
- Soft: —

**Description:**

Implement the `conversations` table (explicit: id, user_a_id, user_b_id, created_at, updated_at) and `messages` table (id, conversation_id, sender_id, recipient_id, original_text, original_language, translated_text, translated_language, created_at). Implement POST /conversations/{conversation_id}/messages (sender_id, recipient_id, original_text, original_language) endpoint. Call a translation API (TBD: Claude, Google Translate, or other — Queen has vendor concerns). Store both original and translated text. Return the message object on success. Include auth check: only the sender can create messages, and only users in the conversation can read.

**Acceptance:**
- messages and conversations tables exist with correct schema
- POST /conversations/{id}/messages requires valid auth (sender is logged-in user)
- POST /conversations/{id}/messages requires sender_id and recipient_id to both exist in users table
- POST /conversations/{id}/messages calls translation API and stores both original and translated text
- POST /conversations/{id}/messages returns 201 and the message object
- original_language is inferred from the user's language_preference; translated_language is inferred from the recipient's language_preference
- Message is persisted and queryable immediately after creation

**Risk:**

Translation API latency. If the chosen API is slow (>2s), consider async. For MVP, sync is acceptable but the ticket may need to split into async in v1.1. Confirm translation provider and latency SLA with the Queen before starting. If the team chooses implicit conversation pairs instead of explicit conversations table, this ticket shrinks (remove conversations table, use (sender_id, recipient_id) as composite key on messages). Confirm schema choice with the Cat.
