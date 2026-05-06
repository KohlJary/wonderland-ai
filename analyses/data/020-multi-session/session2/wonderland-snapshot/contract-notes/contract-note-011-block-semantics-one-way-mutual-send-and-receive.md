## Contract Note 011: Block semantics: one-way blocks, mutual visibility filter, message-send validation

**State:** proposed
**Contract Version:** block-semantics v1 (one-way blocks with symmetric visibility filter; send validation)

**Current Shape:**

N/A (blocking is new); conversation-schema v1 has no block state.

**Proposed Change:**

Clarify the semantics of blocking for the frontend/backend seam:

(A) **One-way blocks**: BlockedParticipants(conversation_id, blocker_id, blocked_id) allows (blocker=A, blocked=B) independent of (blocker=B, blocked=A). User A can block User B without User B blocking User A. This is one-way blocking and matches the story ("Maya revokes access to one participant mid-flight").

(B) **Symmetric visibility filter**: Despite one-way block records, the message-visibility check (contract-note-010) is symmetric: "User A sees message from User B if neither (A blocked B) nor (B blocked A)." This means:
- If A blocks B, then A cannot see B's messages.
- If B blocks A, then B cannot see A's messages.
- If both block each other, neither sees the other's messages.
- If neither blocks, both see all messages.

(C) **Message-send validation**: When User A attempts to POST /conversations/{id}/messages, check "is User A blocked by the peer?" If BlockedParticipants exists where (blocker=peer, blocked=A), reject with 409 or 403 "you are blocked by this user." This is observable: blocked user knows they're blocked because sends fail. Unblocked users can always send (even if they have blocked the peer; they can send, but the peer won't see it due to visibility filter in contract-note-010).

(D) **Audit trail**: Every block and unblock operation writes to blocking_history(conversation_id, blocker_id, blocked_id, action, timestamp, requester_id). Actions: "block" or "unblock". Timestamp and requester_id allow Sam (the operator in Story-008) to verify when the block took effect and who initiated it.

(E) **Idempotent operations**: POST /block where user is already blocked returns 200 (no-op, no duplicate history entry). POST /unblock where user is already unblocked returns 200 (no-op). Frontend can retry freely without worrying about errors.

(F) **Self-block validation**: Prevent user from blocking themselves in the same conversation. POST /conversations/{id}/block {blocked_user_id} where blocked_user_id == caller_user_id returns 400 (invalid). Validation happens at the endpoint before writing to BlockedParticipants.

(G) **Conversation-local blocks**: Blocks are per-conversation, not global. Two users can talk in Conversation A (with block state) and have no block state in Conversation B. Each conversation's block state is independent.

**Source:**

Ticket-007 (extend conversation schema); Ticket-008 (visibility filter); Ticket-009 (block/unblock endpoints); Stories-007 and -008.

**Frontend Impact (Tweedledee):**

_pending_

**Backend Impact (Tweedledum):**

Endpoints needed:
- POST /conversations/{id}/block {blocked_user_id} — caller must be a conversation participant; blocked_user_id must be the other participant; idempotent; writes to BlockedParticipants and blocking_history on first call.
- POST /conversations/{id}/unblock {blocked_user_id} — caller must be a conversation participant; idempotent; clears BlockedParticipants row (or marks as unblocked) and writes to blocking_history.
- GET /conversations/{id}/blocks — return list of active blocks in this conversation (who blocked whom, when). Optional for v1; may defer to v2 if observability is handled via blocking_history queries.

Validation:
- Caller must be a participant in the conversation (403 if not).
- blocked_user_id must be the other participant (400 if not, or if self-block).
- Block endpoint requires auth; no anonymous blocks.

Error handling:
- 400: invalid input (self-block, non-existent user, malformed request).
- 403: not a participant in the conversation.
- 409: (optional) attempted to send a message while blocked; return conflict with message "you are blocked by this user."

Logging:
- Every block/unblock writes to blocking_history with full context.
- Message-send validation logs blocked-send attempts to audit trail (feeds observability for Sam's ticket-010).

**Resolution:**

_pending Tweedledee response_

