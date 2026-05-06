## Contract Note 009: Block visibility enforcement in message API

**State:** proposed
**Contract Version:** block-enforcement v1 (PROPOSED)

**Current Shape:**

Contracts 001–004 established the message envelope and polling behavior without accounting for block state. When Maya blocks David, the story says Maya stops seeing David's messages; the architecture does not yet specify how this is enforced (query filter? response filter? real-time filter?). Ticket-008 says GET /conversations/{id}/messages must enforce block visibility, but the exact point of enforcement is open.

**Proposed Change:**

Block enforcement happens at **query time, not serialization time**. When the frontend calls GET /conversations/{id}/messages, the backend query includes a WHERE clause that filters out:
- messages from users who have blocked the querying user, AND
- messages from the querying user to users they have blocked.

The query is:

```
SELECT * FROM messages m
WHERE m.conversation_id = ? 
  AND m.sender_id NOT IN (
    SELECT blocked_id FROM blocks 
    WHERE conversation_id = ? AND blocker_id = ?
  )
  AND (
    m.sender_id = ? OR m.sender_id NOT IN (
      SELECT blocked_id FROM blocks 
      WHERE conversation_id = ? AND blocker_id = ?
    )
  )
```

Simplified: return messages where the sender is either the current user, or the sender has not blocked the current user, and the current user has not blocked the sender. If the querying user is themselves blocked (from the conversation), return an empty result set. The filter is **silent**: no error returned; the frontend sees an empty list and treats it the same way it treats an empty conversation (graceful degradation per contract-note-004).

**Source:** Ticket-008 acceptance criteria; Story 004 (Maya's block of David mid-conversation); Story 006 (Sam's observability requirement that block enforcement is trackable).

**Frontend Impact (Tweedledee):**

From the frontend's standpoint, when Maya blocks David:
- Existing messages from David in Maya's message list are no longer returned by the API poll.
- The frontend's message cache updates on the next poll (every 2 seconds per contract-note-002).
- Maya sees the message list shrink; David's messages disappear silently.
- No error is returned; the frontend treats the empty-message case the same way it treats any empty response (showing "no messages" or "conversation empty" per the empty UI state already implemented in contract-note-007/contract-note-003).

**Concern for refinement:** The stories contradict on retroactivity. Story 004 (Maya) says existing messages are hidden; Story 005 (Klaus) says retroactively hidden. These are the same operation with different expectations. I'm proposing that the block always hides existing messages retroactively (the query filter applies to all messages). If the team instead wants Maya's block to hide future messages only while leaving existing messages visible to David, that changes the contract and requires a decision at the architecture level. The proposed change assumes retroactive visibility change; Story 005 (Klaus) resolves into the query-filter model, but Story 004 (Maya) may not align. **Suggest Cat review Stories 004 and 005 to confirm retroactive hiding is the intended model.**

**Backend Impact (Tweedledum):**

_Pending_

**Resolution:**

_Pending Tweedledum's assessment and response._
