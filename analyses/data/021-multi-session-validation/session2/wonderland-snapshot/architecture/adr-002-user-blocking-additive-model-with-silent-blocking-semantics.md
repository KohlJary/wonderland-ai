# ADR-002: User blocking: additive model with silent blocking semantics

## Context

Feature scope: user A can block user B, preventing B from sending messages to A and hiding B's messages from A's view. The block is bidirectional in effect (neither party can message the other) but unidirectional in control (only A can unblock). The existing Message and Conversation models have no blocking surface; blocking must be enforced at the API boundary (send endpoint) and query boundary (list endpoint) without exposing the block to the blocked user (silent blocking).

## Decision

Add a Block table to models.py with columns: id (UUID PK), blocker_id (FK to User), blocked_id (FK to User), created_at (timestamp). Add unique constraint (blocker_id, blocked_id) to prevent duplicate blocks. No soft-delete on Block; blocks are ephemeral (hard-delete on creation and deletion). At message send time (POST /chats/{conversation_id}/messages), query Block table before persisting: if Block exists with (blocker=recipient, blocked=sender), return 403 Forbidden with detail 'you are blocked by this user'. At message list time (GET /chats/{conversation_id}/messages), filter messages with a LEFT JOIN to Block: exclude rows where Block.blocker_id = requester_id. Conversation entity itself remains queryable (does not soft-delete); the conversation returns 200 OK with an empty message list if a block is active. Add three new endpoints: POST /blocks/{blocked_user_id} (create block, owned by blocker), GET /blocks (list blocks created by current user), DELETE /blocks/{blocked_user_id} (unblock, owned by blocker). Only the blocker can unblock.

## Tradeoffs

- Silent blocking (blocked user receives 403 on send but is never told they are blocked, only sees their messages as undelivered). This is privacy-friendly but potentially confusing. Mitigate with clear error message in frontend UI: 'This user is not accepting messages from you.'
- Conversation entity persists (blocked user can still see conversation_id in their conversation list) but returns no messages. Alternative: soft-delete the conversation for the blocked user's view. Current choice is simpler (no soft-delete join overhead) and more honest (you don't hide the relationship; you just silence it).
- Blocking is permanent until unblocked (no auto-expiration, no block reasons, no appeal flow). Per directive scope, these are deferred. Permanent blocking is the simplest model.
- No audit trail of blocks visible outside the blocker. Blocks are not logged to system audit table; only the blocker sees their Block records. This is privacy-friendly but means the platform cannot audit who is blocking whom (compliance-relevant if users report blocking abuse). Current model assumes blocks are user control, not platform concern. Open: does compliance need visibility into blocks for abuse investigation? If yes, add block audit trail in fast-follow.
- Block enforcement at two boundaries (send endpoint + query filter) requires coordination. Mitigate: define a shared `is_blocked(blocker_id, blocked_id)` utility function and use it in both places.
- GDPR deletion: when a user is deleted, their Block records (as blocker_id) are hard-deleted. This is correct (blocker's action is gone; blocked user is unblocked). If a blocked_id user is deleted, their corresponding Block records are also hard-deleted (no dangling FKs, and blocked user doesn't retain a record of who blocked them). This is the right choice.

## Status

Proposed
