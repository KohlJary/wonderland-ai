## Ticket 007: Backend: Extend Conversation schema with participant block state

**Sources:** story: moderator-blocks-a-bad-faith-participant-mid-conversation, story: technical-peer-revokes-collaboration-after-discovering-incompatible-working-style
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 80% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: backend-message-schema-with-translation-state-machine
- Blocked by: —
- Soft: —

**Description:**

Conversation.participants becomes a list of {user_id, blocked_at, blocked_by}. blocked_at and blocked_by are nullable (unblocked). Schema migration is backward-compatible: existing conversations default to unblocked participants. Add a blocking_history table to audit when blocks occur. No UI work; schema-only.

**Acceptance:**
- Conversation.participants list includes block state for each user
- blocking_history table exists and records (conversation_id, blocker_id, blocked_id, blocked_at)
- Existing conversations load with unblocked state
- Migration is reversible

**Risk:**

If we later need to distinguish block reasons ("spam" vs "incompatible"), the schema needs a reason field. Add it now as nullable to avoid a second migration.
