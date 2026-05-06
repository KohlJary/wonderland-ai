## Contract Note 008: Block enforcement at message send and list

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

No blocking contract yet. Message send (POST /chats/{chat_id}/messages) and list (GET /chats/{chat_id}/messages) have no block checks.

**Proposed Change:**

Add block enforcement at two boundaries: (1) message send endpoint checks Block table within transaction before persisting message; (2) message list endpoint filters messages with LEFT JOIN to Block table. Block management endpoints POST/GET/DELETE /blocks/{user_id}.

**Source:** ADR-002 (user blocking feature), Directive from Dodo asking for contract on block-check placement and atomicity

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

Backend owns Block table persistence, block-state queries, and message send gate. Here's the detailed contract:

**Block table schema:**
- id (UUID, primary key)
- blocker_id (UUID, FK to User)
- blocked_id (UUID, FK to User)
- created_at (timestamp, default now())
- Unique constraint: (blocker_id, blocked_id) — prevents duplicate blocks
- No soft-delete; blocks are hard-deleted on unblock

**Message send gate (POST /chats/{chat_id}/messages):**
Within a single database transaction:
1. Validate sender_id (from auth token) is in the conversation
2. Query Block table: SELECT 1 FROM blocks WHERE blocker_id = conversation.recipient_id AND blocked_id = sender_id
3. If row exists, rollback transaction and return 403 Forbidden with detail 'you are blocked by this user'
4. If no row, INSERT message into messages table with translation_status='pending'
5. Enqueue async translation job (fire-and-forget, outside txn)
6. Commit txn and return 200 with message object

Rationale: block check must be atomic with message write to prevent race condition where block is created between check and write. Atomic = same database transaction. Async translation job is fire-and-forget outside the txn (translation failure doesn't block message persistence).

**Message list (GET /chats/{chat_id}/messages):**
Query:
```sql
SELECT m.* FROM messages m
LEFT JOIN blocks b ON (b.blocker_id = ? AND b.blocked_id = m.sender_id)
WHERE m.chat_id = ? AND b.id IS NULL
ORDER BY m.created_at ASC
```
Variable 1 = requester_id (from auth token). This filters out messages where requester_id is the blocker and m.sender_id is the blocked user. Conversation entity persists (200 OK, empty message list if all messages are filtered).

**Block endpoints:**
- POST /blocks/{blocked_user_id}: Create a block. Request is empty body. Response: { id, blocker_id, blocked_id, created_at }. Only the authenticated user (blocker) can block; cannot block self (return 400). Cannot block the same user twice (return 409 Conflict if block already exists).
- GET /blocks: List all blocks created by the authenticated user. Response: [ { id, blocker_id, blocked_id, created_at }, ... ]
- DELETE /blocks/{blocked_user_id}: Unblock. Only the blocker can unblock. On success, hard-delete the Block record and return 204 No Content. On 404 (block doesn't exist), return 404.

**Error semantics:**
- 403 Forbidden on message send if user is blocked: frontend should display 'This user is not accepting messages from you.' (ADR-002 specifies silent blocking—blocked user is not told they are blocked, only that send failed).
- 400 Bad Request if attempting to block self on POST /blocks
- 409 Conflict if attempting to create a duplicate block

**Invariants enforced:**
- Block records are never null (hard-delete only)
- Block check on message send is atomic with message persistence (same txn)
- Block list filters messages at query time (no denormalization; block state is source of truth)
- Conversation persists even if all messages are blocked (no soft-delete of conversation)

**Known limitations:**
- Block enforcement requires a database transaction; if the backend uses an ORM that doesn't support txns well (unlikely), this becomes harder. Flag if that's a concern.
- Blocked user sees a 403 on send but is not told why. Frontend must handle this gracefully with the error message from the response body.
- No block audit trail visible to platform (only the blocker sees their Block records). If compliance needs visibility, add audit table in fast-follow.
