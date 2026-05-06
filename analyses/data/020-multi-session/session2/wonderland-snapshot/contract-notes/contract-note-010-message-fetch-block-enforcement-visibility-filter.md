## Contract Note 010: Message-fetch block enforcement and visibility filter

**State:** proposed
**Contract Version:** message-visibility v2 (extends polling v1 with block-state filtering)

**Current Shape:**

GET /conversations/{conversation_id}/messages (contract-note-006) returns all messages where caller is a conversation participant. Membership check: caller is user_a OR user_b. No block filtering.

**Proposed Change:**

Extend the membership check with block-state visibility. When User A calls GET /conversations/{id}/messages: (1) Check User A is a participant. (2) Check block state: for each Message in the conversation, hide it if User A has blocked the sender OR the sender has blocked User A. Return only visible messages (those from unblocked senders). The result may be an empty list if User A is the only sender or if all peer messages are from blocked senders.

Visibility rule: User A sees messages from sender User B if and only if neither (A blocked B) nor (B blocked A). This is symmetric in the block check but asymmetric in the results: if A has blocked B but B hasn't blocked A, then A sees nothing from B, but B still sees messages from A (B is not blocked, so the check passes for B).

This is the "silent enforcement" model from Ticket-008: no error message. Just return what's visible. Empty list means either there are no messages, or all peer messages are blocked from this caller's perspective.

**Source:**

Ticket-008 (GET /conversations/{id}/messages enforces block visibility); Stories-007 and -008 (block-based revocation; operator observability).

**Frontend Impact (Tweedledee):**

_pending_

**Backend Impact (Tweedledum):**

Query changes from contract-note-006's stateless fetch to a filtered fetch. Current query (pseudocode):

```sql
SELECT * FROM Message WHERE conversation_id = ? 
ORDER BY created_at DESC
```

New query adds block-state filtering:

```sql
SELECT m.* FROM Message m
WHERE m.conversation_id = ?
  AND NOT EXISTS (
    SELECT 1 FROM BlockedParticipants bp
    WHERE bp.conversation_id = m.conversation_id
      AND (
        (bp.blocker_id = ? AND bp.blocked_id = m.sender_id)
        OR (bp.blocker_id = m.sender_id AND bp.blocked_id = ?)
      )
  )
ORDER BY m.created_at DESC
```

This join is expensive if BlockedParticipants is large, but for 2-user conversations (at most 2 rows per conversation), it's negligible. Consider a service-layer helper: `block_is_active(conversation_id, user_a, user_b)` that checks both directions; reuse in message-fetch and message-send.

Response shape unchanged (contract-note-001 / contract-note-006): same Message envelope, just fewer rows in the array (blocked senders' messages omitted). Caller cannot detect whether a missing message was hidden due to block or never existed (silent enforcement).

Polling behavior (contract-note-006) unchanged: frontend still polls every 2 seconds; backend returns visible messages (same query on each poll). If messages are filtered out (sender is blocked), frontend sees them disappear from the list; frontend should handle this gracefully (log, optionally show "peer has been blocked" badge — exact UX is Tweedledee's).

**Resolution:**

_pending Tweedledee response_

