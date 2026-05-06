## Contract Note 010: Blocked conversation visibility in UI

**State:** proposed
**Contract Version:** blocked-conversation-ui v1 (PROPOSED)

**Current Shape:**

Contract-note-003 specifies that the frontend renders messages based on sender/receiver role; contract-note-004 specifies that failed translations show "original only" state. The blocked-conversation case is a third invisible state: the API returns an empty list because the querying user is blocked from the conversation.

**Proposed Change:**

When a block is in effect and the frontend polls GET /conversations/{id}/messages:
1. If the querying user is blocked from the conversation (they cannot see any messages), the API returns an empty list (silent, no error).
2. The frontend treats this the same way it treats the "empty conversation" state—showing a message like "No messages in this conversation" or "Conversation empty."
3. The frontend does NOT distinguish between "conversation is actually empty" and "you are blocked from this conversation." Both show the same UI state. This is intentional: we do not leak information about whether a block is in effect.
4. If the querying user can see some messages but not others (because they have blocked or been blocked by some participants), the frontend simply does not render those messages. They are absent from the list; no "deleted" or "hidden" marker appears.

**Source:** Story 004 (Maya blocks David and no longer sees his messages); Story 006 (Sam confirms blocks are enforced without seeing message content); contract-note-007 (empty conversation state already implemented).

**Frontend Impact (Tweedledee):**

The frontend already has an "empty conversation" UI state (contract-note-007 named it as a reachable state for the message-render component). When a block is applied and the message list becomes empty, the same UI state renders. No new UI state is needed. The frontend's message cache updates on each poll; if messages disappear from the response due to a block, the cache no longer contains them, and the component re-renders the empty state.

One consideration: if the user is blocked mid-session (another user blocks them while they're viewing the conversation), the frontend will see the message list shrink on the next poll. The transition is silent—no notification, no "you were blocked" alert. The UX is that the conversation becomes empty. This aligns with the silent-enforcement model in contract-note-009.

**Backend Impact (Tweedledum):**

_Pending_

**Resolution:**

_Pending Tweedledum's assessment and response._
