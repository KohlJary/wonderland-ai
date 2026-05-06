## Contract Note 007: User blocking and message gating

**State:** proposed (awaiting backend response)
**Contract Version:** (unlocked)

**Current Shape:**

Cat's ADR proposes blocking table with dual-enforcement: gate on message send (403 when blocked), filter on message list (silent mute). Contract shape is unspecified; this note anchors the seam.

**Proposed Change:**

Three load-bearing details:
1. **Block check timing on message send:** does the check fire before or after message is persisted? (impacts whether a blocked user can accidentally persist a message before the gate rejects it)
2. **Message list filtering:** is filtering applied at query time (in the SQL WHERE clause), or are blocked messages stored and filtered by frontend?
3. **Real-time block events:** when user A blocks user B, do both users receive a WebSocket event, or is blocking read-only (no real-time notification)?

**Source:** Cat's blocking ADR (additive model, silent blocking). Ticket 007 (blocking endpoints) depends on this contract. Risk: if block check is not properly gated on send, a blocked user might persist messages before receiving 403.

**Frontend Impact (Tweedledee):**

I'm building blocking UI: "Block user" button visible on messages from other users. Clicking sends POST /blocks/{user_id}. On success, that user's messages disappear from my list (either via local filtering or WebSocket event). I also need:
1. A "Blocked users" page (GET /blocks list) showing users I've blocked.
2. "Unblock" button on each blocked user (DELETE /blocks/{user_id}).
3. Handling for the edge case: what if I try to send a message to someone who has blocked me? The post should fail with 403 "you are blocked by this user" (per the ADR). I'll show an error toast: "You cannot send messages to this user (you are blocked)."

**Questions and assumptions:**

1. **Block check timing:** When I POST /chats/{chat_id}/message with original_text, the backend should check *before* persisting: is this user blocked by the recipient? If yes, return 403 immediately. **I'm assuming the block check is synchronous and happens before the message is persisted.** If the check happens after persist (so a message might briefly exist before being rejected), that's a race condition—frontend would render my message, then get a 403, then have to remove it. That's poor UX. Confirm: does the block gate fire *before* INSERT?

2. **Message list composition:** When I fetch GET /chats/{chat_id}/messages, I assume the response already filters out messages from users who have blocked me. **I am assuming filtering happens server-side** (in the SQL WHERE clause). If I have to do client-side filtering, I need to know: do I get a list of users who have blocked me, or do I receive the full message list and parse it to infer which senders are blocked?

3. **Real-time block events:** When user B blocks me, do I receive a WebSocket event? Or do I only learn about the block when I try to send a message and get 403? **I'm assuming blocking is silent** (no real-time notification to the blocked user), per the ADR's "silent mute" semantic. This means:
   - User A blocks User B: User A's list is immediately cleaned up (either via local filtering or I re-fetch).
   - User B does NOT get a notification that they were blocked; they find out when they try to send the next message and get 403.
   - This is acceptable for MVP (avoids the "user sees they were blocked" notification event).

4. **Conversation persistence after block:** Per the ADR, the conversation entity persists (returns 200 with empty message list) if I'm blocked. **I'm assuming GET /chats/{chat_id}/messages returns 200 with an empty list**, not 403 or 404. This means I can keep the conversation window open; the list is just empty and stays empty until I'm unblocked. Confirm: does conversation remain accessible (200 + empty list) or become inaccessible (403/404)?

5. **Block enumeration during login:** When I log in, do I get a list of users who are blocking me? Or do I find out only when I encounter a 403 on message send? **I'm assuming I don't get a preemptive list**—I find out on send attempt. This keeps login faster and simpler.

**Client state for blocking:**

- `blocked_users: [ user_id, ... ]` — users I have blocked (populated from GET /blocks)
- `is_blocked_by_recipient: boolean` — inferred from error response on message send (when I get 403 "you are blocked by this user")
- When I block a user: remove all their messages from the local message list, add user_id to blocked_users list
- When I receive a 403 on message send: set is_blocked_by_recipient = true, show error toast, disable send button with message "You are blocked by this user"

**UI states affected:**

- **Blocked users list:** GET /blocks returns list of blocked users; I render a "Blocked users" page with unblock buttons
- **Message send error:** when POST /chats/{chat_id}/message returns 403 "you are blocked by this user", I show error toast and set send disabled
- **Message list after block:** when I POST /blocks/{user_id}, I either (a) locally filter messages from that user, or (b) re-fetch the message list to see the backend-filtered version. I'm leaning toward (a) for UX (immediate feedback), but confirm if backend filtering is required.

**Backend Impact (Tweedledum):**

Backend owns the Block table, block endpoints, and dual-enforcement gates. Specifically:

**Block table schema:**
- blocker_id (FK to User, NOT NULL)
- blocked_id (FK to User, NOT NULL)
- created_at (timestamp, auto-set)
- PRIMARY KEY (blocker_id, blocked_id) — unique constraint prevents duplicate blocks
- No deleted_at or soft-delete; blocks are hard-deleted on unblock or account deletion

**POST /blocks/{user_id} (create block):**
- Request: header `Authorization: Bearer <session_token>`, path param user_id
- Response (201): `{ blocker_id, blocked_id, created_at }`
- Backend: insert into Block (blocker_id=current_user, blocked_id=user_id). If already blocked, return 409 Conflict (or 200 if idempotent is preferred).
- **Question:** should POST /blocks be idempotent (return 200 if already blocked) or return 409 on duplicate? I'm assuming 409 (explicit error on double-block) so frontend knows whether it's new.

**GET /blocks (list my blocks):**
- Request: header `Authorization: Bearer <session_token>`
- Response (200): `[ { blocker_id, blocked_id, created_at }, ... ]` (list of users I have blocked)
- Backend: query Block where blocker_id = current_user

**DELETE /blocks/{user_id} (unblock):**
- Request: header `Authorization: Bearer <session_token>`, path param user_id
- Response (204 No Content, or 200 if you prefer)
- Backend: delete from Block where blocker_id = current_user AND blocked_id = user_id. Idempotent (if not found, return 204 anyway).

**Gate 1: Message send (POST /chats/{chat_id}/message):**
- **Before persisting the message**, check: is current_user blocked by the recipient?
- Query: `SELECT 1 FROM Block WHERE blocker_id = recipient_id AND blocked_id = current_user LIMIT 1`
- If found: return 403 `{ error: "you are blocked by this user" }`
- If not found: proceed to persist message (per contract 004: INSERT with translation_status='pending')
- **Timing is critical:** block check must fire before INSERT. If a message is persisted first and then rejected, frontend has a race condition.

**Gate 2: Message list (GET /chats/{chat_id}/messages):**
- **When retrieving messages**, filter out any where the sender has blocked the current_user
- Query: `SELECT messages.* FROM messages WHERE chat_id = ? AND deleted_at IS NULL AND sender_id NOT IN (SELECT blocker_id FROM Block WHERE blocked_id = current_user AND blocker_id IS NOT BLOCKED_BY_ME) ...`
- Wait, this is subtle. Let me clarify the two-way semantics:
  - I blocked User B: I should not see messages from User B.
  - User B blocked me: I should not send to User B (enforced by Gate 1), but should I see messages I already sent to User B before they blocked me?
  
  **The ADR says blocking is unidirectional and the blocked user doesn't see a 404.** I interpret this as:
  - I (User A) block User B: messages from B disappear from my message list.
  - User B blocks me: I can still see my own conversation (my own messages persist), but I can't send new messages to B.
  
  So the filter is: `messages where sender_id NOT IN (users who have blocked me)` — i.e., I don't see messages from blockers, but I do see my own messages.

- **Question:** confirm the filtering logic. Should current_user see messages they sent before being blocked, or should the entire message list become empty if blocked?

**Account deletion cascade:**
- When a user account is deleted (GDPR 17), hard-delete all Block records where blocker_id = user_id OR blocked_id = user_id
- This clears the user out of both sides of the block relationship (users they blocked + users who blocked them)

**Invariants enforced:**
- A user cannot block themselves (blocker_id != blocked_id, add CHECK constraint or application-level validation)
- Block is unidirectional (if A blocks B, B can block A separately; these are independent)
- A blocked user cannot send messages to the blocker (enforced by Gate 1 before persist)
- A user does not see messages from their blockers in the message list (enforced by Gate 2 filter)
- Blocking does not affect the conversation entity (conversation persists, just message list may be empty)

**Known limitations:**
- No "unblock notification": when A unblocks B, B doesn't get a notification. B only notices if A sends a new message.
- No "I blocked you" notification: when A blocks B, B doesn't know. B finds out if they try to send a message (403).
- No temporal visibility: if B was blocked by A for a period, then unblocked, B can see all messages B sent before being blocked. (Acceptable for v1; more sophisticated timestamped visibility is a future feature.)
- Block enumeration is not real-time: if A blocks B while B is composing a message, B's message may still be sent before B receives the rejection. This is a race condition inherent in the stateless client architecture. Acceptable for v1.

**Questions for Tweedledee:**
1. Block check timing: confirm that the block gate fires *before* INSERT /chats/{chat_id}/message. If timing is async or post-insert, the frontend race condition is unavoidable.
2. Message list filtering: confirm that GET /chats/{chat_id}/messages returns 200 with empty list (not 403) if the current user is blocked.
3. Filter semantics: should a blocked-and-then-unblocked user see messages they sent during the block period? (I'm assuming yes—the messages never disappear, just the visibility changes.)
4. POST /blocks idempotence: should double-block return 409 or 200?

**Resolution:** proposed — awaiting backend response on timing, filtering, and semantics.
