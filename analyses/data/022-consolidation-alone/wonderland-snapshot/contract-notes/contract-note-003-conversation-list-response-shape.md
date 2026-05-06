## Contract Note 003: Conversation list response shape

**State:** agreed
**Contract Version:** v1

**Current Shape:**

No conversations list endpoint yet

**Proposed Change:**

GET /conversations returns list of conversation objects. Response shape per conversation: { id, user_a_id, user_b_id, other_user: { id, display_name, language_preference }, last_message: { id, original_text, original_language, created_at } }. Sorted by last_message.created_at DESC. Frontend uses this to render conversation list (Story 005) with partner name, language they speak, and last message preview.

**Source:** alice story/user-opens-conversation-list-and-resumes-a-prior-conversation

**Frontend Impact (Tweedledee):**

Frontend parses GET /conversations response and renders a conversation list. Each item shows: conversation partner's display_name (from other_user), their language_preference (so user knows what language they speak), last_message preview (original_text + original_language tag). Clicking a conversation item navigates to GET /conversations/{id} to fetch full message history. Last message preview includes original text only (not translation, which is per-recipient view). Original_language tag on preview lets user know what language the preview is in.

**Backend Impact (Tweedledum):**

GET /conversations (authenticated, HTTP Basic) returns list of conversation objects. For each conversation, determine "the other user" (if current_user == user_a_id, other_user is user_b; vice versa). Response shape: [{ id, user_a_id, user_b_id, other_user: { id, display_name, language_preference }, last_message: { id, original_text, original_language, created_at } }]. Sorted by last_message.created_at DESC. Invariant: user sees only conversations they are party to (WHERE user_a_id = current_user OR user_b_id = current_user). Performance: single query with JOINs; no pagination in v1 (acceptable for MVP; add in v1.1 if needed).

**Resolution:** Agreed v1. Last message preview shows original text + original_language tag (not translation, which is per-recipient). Response includes other_user object with display_name and language_preference so user sees who the conversation is with and what language they speak.

---

**History:**

- **2024-01-XX (Tweedledee propose):** Initial proposal with response shape including other_user and last_message.
- **2024-01-XX (Tweedledum propose as note-006 in parallel):** Proposed same endpoint; raised clarifying questions about preview language tag and which version of message (original vs translation).
- **2024-01-XX (Tweedledee consolidate and mark agreed):** Confirmed preview should include original_language tag; original text only (not translation); marked agreed pending backend confirmation.
