## Contract Note 003: Message model and GDPR deletion semantics

**State:** proposed (awaiting resolution)
**Contract Version:** (unlocked)

**Current Shape:**

ADR assumes messages persisted indefinitely unless deleted by subject request (GDPR 17). Audit trail is system-only (not exposed via API). Deletion must cascade to translation service cache (if cached) and message records.

**Proposed Change:**

Frontend needs explicit contract on message storage and deletion: (A) Message model includes sender_id (User FK), recipient_id (User FK), original_text, translated_text, language_pair, created_at, updated_at, deleted_at (soft-delete); (B) frontend never deletes messages directly; deletion is triggered by user via a DELETE /messages/{message_id} endpoint, which is soft-delete at DB level; (C) deleted messages do not appear in GET /conversations/{conversation_id}/messages; (D) if user account is deleted (GDPR 17), deletion endpoint cascades to all messages with that sender_id. Frontend UI should show a message delete button (for user's own messages only) with confirmation.

**Source:** ticket:schema-and-persistence-layer + ADR tradeoff on message persistence and deletion compliance. GDPR deletion scope unclear; needs Queen review, but frontend contract is straightforward.

**Frontend Impact (Tweedledee):**

I'm building message list UI with optional delete button (visible only for current user's messages). Clicking delete sends DELETE /messages/{message_id}. On success, remove message from local list and re-fetch conversation (or subscribe to deletion event if real-time). If deletion fails (e.g., already deleted), show error toast. No other deletion semantics exposed to frontend.

**Backend Impact (Tweedledum):**

Soft-delete semantics with cascading deletion support. Here's the contract:

**Message table schema:**
- message_id (UUID primary key)
- conversation_id (FK to Conversation)
- sender_id (FK to User)
- recipient_id (FK to User, inferred from conversation.user_2_id if sender = user_1; otherwise user_1)
- original_text (text, NOT NULL)
- original_language (enum: 'EN', 'DE', 'JA', NOT NULL)
- translated_text (text, nullable; null if translation_status is 'pending' or 'failed')
- translation_status (enum: 'pending', 'translated', 'failed', default 'pending')
- translation_error (text, nullable; populated if translation_status = 'failed')
- created_at (timestamp, NOT NULL, auto-set)
- updated_at (timestamp, NOT NULL, auto-set on insert/update)
- deleted_at (timestamp, nullable; NOT NULL only if soft-deleted)

**GET /chats/{conversation_id}/messages:**
- Request: `?since=<ISO 8601 timestamp> (optional, for pagination)`
- Response (200): `[ { id, conversation_id, sender_id, original_text, original_language, translated_text, translation_status, created_at, updated_at }, ... ]`
- Backend: query messages WHERE conversation_id = ? AND deleted_at IS NULL, ordered by created_at ASC, paginated
- Deleted messages (deleted_at IS NOT NULL) never appear in the response
- Authorization: user must be one of the two users in the conversation; return 403 if not

**DELETE /messages/{message_id}:**
- Request: header `Authorization: Bearer <session_token>`
- Response (204 No Content on success, or error)
- Backend: query message by id, verify sender_id = current user_id (users can only delete their own messages), UPDATE messages SET deleted_at = now(), return 204
- If message already deleted (deleted_at IS NOT NULL), return 200 OK (idempotent; deletion is not an error)
- If message_id does not exist, return 404 Not Found
- If user is not the sender, return 403 Forbidden

**GDPR Subject request / account deletion cascade:**
- When user account is deleted (via DELETE /auth/user), backend cascade-deletes (soft-delete) all messages where sender_id = user_id
- Schema: add a FOREIGN KEY on messages.sender_id REFERENCES users(user_id) ON DELETE CASCADE, but the delete action is a soft-delete trigger (not a hard delete)
- Implementation: when user.deleted_at is set, a trigger or application logic updates all messages with that sender_id to set deleted_at = now()
- Conversations are also soft-deleted if both users are deleted

**Retrieval by user (message history after deletion):**
- If a user re-creates an account with the same email (allowed in v1 because email verification is out of scope), they get a new user_id
- Old messages (from the previous account) are still soft-deleted and not visible
- There is no "restore" operation; soft-deletion is one-way

**Message ordering:**
- Messages are ordered by created_at ASC (chronological)
- If two messages have the same created_at (unlikely but possible due to clock skew), order is undefined in v1 (acceptable; sequence numbering is deferred to fast-follow)
- Deleted messages do not affect ordering of remaining messages

**Translation cache deletion:**
- We are not caching translations in v1 (per ticket 003), so no cache purge is needed
- If translation caching is added later, deletion of a message must trigger a purge request to the external cache service (e.g., Redis)
- For v1: this is a deferred concern

**Invariants enforced:**
- Every message has exactly one sender (FK to User, NOT NULL)
- Every message belongs to exactly one conversation (FK to Conversation, NOT NULL)
- Deleted messages never appear in API responses (WHERE deleted_at IS NULL filter is always applied)
- Soft-deleted messages are not recoverable via the API (no "undelete" operation)
- A message's deleted_at timestamp can only be set once (no "re-deletion"; the SET operation is idempotent)
- If a message is deleted, its translation (if any) is also logically deleted (frontend sees nothing; backend still has the record)

**Known limitations:**
- No hard-delete means the messages table grows unbounded. For v1, this is acceptable (messages are not huge; a million messages is ~200MB). In production, implement data retention policies (e.g., hard-delete soft-deleted messages after 90 days) via a background job. Defer to fast-follow.
- No message editing: once sent, a message cannot be edited. If editing is needed, add an `edited_at` and `edit_history` field in fast-follow.
- No message reactions, replies, or threading: each message is standalone. Threading is deferred to fast-follow.

**Questions for Tweedledee:**
- On soft-deletion, do you prefer a re-fetch of the entire conversation, or should I emit a WebSocket event `message_deleted` so you can remove it from the local list?
- Do you need to see soft-deleted messages in the UI at all (e.g., "[message deleted by sender]" placeholder), or should they simply vanish?
- For pagination, do you prefer `since` (timestamp-based) or offset/limit (cursor-based)? The `since` approach is simpler and works better with eventual consistency if we ever shard.

**Resolution:** proposed — awaiting frontend feedback on deletion UI and WebSocket event preferences.
