## Contract Note 009: Conversation participants block state schema

**State:** proposed
**Contract Version:** conversation-schema v2 (extends v1 with participant block state)

**Current Shape:**

Conversation v1 has user_a_id and user_b_id. No block state. Membership check is: caller is user_a OR caller is user_b.

**Proposed Change:**

Extend Conversation.participants to carry block state. Proposal: Conversation.participants becomes a list of {user_id, blocked_at, blocked_by, block_reason}. blocked_at is a nullable timestamp (null = unblocked); blocked_by is the user_id of the blocker (null = unblocked); block_reason is a nullable string for future extensibility (Story-007 and Story-008 don't require it yet, but add it now to avoid a second schema migration later).

Alternatively: keep Conversation.participants simple (just user_id list) and store all block state in a separate BlockedParticipants table with (conversation_id, blocker_id, blocked_id, blocked_at, block_reason) rows. Proposal: use BlockedParticipants table for clarity and audit trail. Conversation.participants remains the user_id list; block state is queried separately. This separates the concerns: "who is in this conversation?" vs. "who has blocked whom?"

**Source:**

Ticket-007 (extend conversation schema with block state); Stories-007 and -008 (block-based revocation and observability).

**Frontend Impact (Tweedledee):**

_pending_

**Backend Impact (Tweedledum):**

Schema migration: Conversation table unchanged OR add a participants column with JSONB type containing [{user_id, blocked_at, blocked_by, block_reason}]. Recommend: create BlockedParticipants table (conversation_id FK, blocker_id FK, blocked_id FK, blocked_at timestamp NOT NULL, block_reason text nullable) with composite primary key (conversation_id, blocker_id, blocked_id). This allows one-way blocks (A blocks B independent of B blocking A) and audit trail via blocking_history table (separate, for historical records).

Index: (conversation_id, blocker_id) and (conversation_id, blocked_id) for fast lookups when checking "is User X blocked in this conversation?"

Backward compatibility: existing conversations have no BlockedParticipants rows; block check queries return no matches (treated as unblocked). Migration is reversible: drop BlockedParticipants table, existing conversations revert to unblocked state.

Membership check cost: every message-fetch and message-send now requires a block-state lookup. Negligible for 2-user conversations; negligible for all conversations if indexed properly.

**Resolution:**

_pending Tweedledee response_

