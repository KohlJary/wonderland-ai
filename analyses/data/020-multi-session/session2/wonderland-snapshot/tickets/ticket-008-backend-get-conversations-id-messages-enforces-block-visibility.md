## Ticket 008: Backend: GET /conversations/{id}/messages enforces block visibility

**Sources:** story: moderator-blocks-a-bad-faith-participant-mid-conversation
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: backend-get-conversations-id-messages-api-with-translation-status
- Blocked by: ticket: backend-extend-conversation-schema-with-participant-block-state
- Soft: ticket: backend-translation-service-integration-and-async-status-update

**Description:**

The message API query adds a participant visibility check: when User A requests messages from Conversation X, filter out messages from any User B where B has blocked A OR A has blocked B. Return empty list if querying user is blocked from the conversation. Log the query and any blocks encountered for audit (feeds ticket: backend-logging-and-audit-trail-for-translation-events).

**Acceptance:**
- Blocked user cannot retrieve messages sent by blocking user
- Blocking user cannot retrieve messages sent by blocked user
- Empty message list returned if querying user is blocked from conversation
- Block enforcement is silent (no error message leaked about block existence)

**Risk:**

Silent enforcement (no error on block) may confuse the UI about why messages disappeared. Frontend should handle empty response gracefully; it already does from the translation-failed state handling.
