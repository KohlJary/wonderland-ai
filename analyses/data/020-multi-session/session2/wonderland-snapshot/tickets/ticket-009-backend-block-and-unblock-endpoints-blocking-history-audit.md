## Ticket 009: Backend: Block and unblock endpoints + blocking_history audit

**Sources:** story: technical-peer-revokes-collaboration-after-discovering-incompatible-working-style
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 70% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket: backend-extend-conversation-schema-with-participant-block-state
- Soft: ticket: backend-get-conversations-id-messages-api-with-translation-status

**Description:**

POST /conversations/{id}/block with {blocked_user_id} to initiate block. POST /conversations/{id}/unblock with {blocked_user_id} to revoke. Both require auth (caller must be in conversation). Both log to blocking_history with timestamp and requester. Blocks take effect immediately; blocked user sees empty message list on next poll. Unblock is same mechanism in reverse.

**Acceptance:**
- POST /block sets blocked_at timestamp and blocked_by user_id
- POST /unblock clears blocked_at and blocked_by (sets to null)
- Both endpoints require auth; non-conversation-members get 403
- blocking_history records every block and unblock with full context
- Idempotent: blocking an already-blocked user returns 200 (no-op)
- Idempotent: unblocking an unblocked user returns 200 (no-op)

**Risk:**

Self-block (user blocks themselves) is technically allowed by this schema but nonsensical. Add validation: blocker_id != blocked_id. Also: blocks are conversation-local, not global—same two users can talk in a different conversation. Spec is explicit about this in the stories.
