## Contract Note 006: Conversation list endpoint: shape of GET /conversations response

**State:** agreed
**Contract Version:** v1 (conversation list: [{ id, user_a_id, user_b_id, other_user: { id, display_name, language_preference }, last_message: { id, original_text, original_language, created_at } }], sorted by last_message.created_at DESC)

**Current Shape:**

No conversations list endpoint yet.

**Proposed Change:**

GET /conversations returns all conversations for the logged-in user. Each item includes: conversation_id, other_user_id, other_user_display_name, other_user_language_preference, last_message_timestamp, last_message_preview (first 50 chars of original text). Sorted by last_message_timestamp descending. Question: should the preview include language tag (so frontend knows which language the preview is in)? Should it include both original and translated preview, or just one?

**Source:** ticket/list-user-s-conversations-with-last-message-preview and story/user-sees-their-own-conversation-list-and-can-pick-which-one-to-read

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

Straightforward query: SELECT all conversations WHERE user_a_id = current_user OR user_b_id = current_user. JOIN with messages to get last message. Order by created_at DESC. Include language preference from the other user. Small performance risk if user has hundreds of conversations; pagination in v1.1.

**Resolution:**

Agreed. Last message preview shows original text + original_language tag (not translation, which is per-recipient). Response includes other_user object so frontend knows who the conversation is with and what language they speak. Frontend parses and renders conversation list with partner name, language, and last message preview.
