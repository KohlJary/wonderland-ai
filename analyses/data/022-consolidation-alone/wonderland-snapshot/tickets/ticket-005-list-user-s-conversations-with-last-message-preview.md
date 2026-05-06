## Ticket 005: List user's conversations with last-message preview

**Sources:** story/user-sees-their-own-conversation-list-and-can-pick-which-one-to-read
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket/initiate-a-new-conversation-with-another-user, ticket/create-messages-and-conversations-schema-add-send-message-endpoint
- Soft: —

**Description:**

Implement GET /conversations endpoint. Return all conversations for the logged-in user, each with conversation_id, the other user's display_name and language_preference, last_message_timestamp, last_message_preview (first 50 chars of original text). Sort by last_message_timestamp descending. Auth check: user can only see their own conversations.

**Acceptance:**
- GET /conversations returns 200 and a list of all conversations for the logged-in user
- Each conversation includes conversation_id, other_user display_name, language_preference, last_message_timestamp, last_message_preview
- List is sorted by last_message_timestamp (most recent first)
- User can only see their own conversations (auth check)
- Empty conversation list (no conversations yet) returns 200 with empty array

**Risk:**

Low. Query + sort + auth check. Performance risk if user has many conversations; for MVP, acceptable. Consider pagination in v1.1.
