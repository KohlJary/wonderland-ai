## Ticket 004: Message send/receive pipeline (WebSocket or polling v1)

**Sources:** story:exchange-messages-with-a-german-speaker, story:exchange-messages-with-a-japanese-speaker
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 2–3 days, 65% confident
**Status:** open

**Dependencies:**
- Blocks: ticket:ui-scaffolding-and-message-render
- Blocked by: ticket:user-registration-and-auth-email--password-v1, ticket:schema-and-persistence-layer, ticket:translation-service-integration-api-client--contract
- Soft: —

**Description:**

Implement real-time message flow: user A sends a message; it is persisted; it is translated; user B receives it. Coordinate with Tweedledum on backend message insertion, translation call, and retrieval. Frontend listens (WebSocket or polling; negotiate with Tweedledum) and renders incoming messages. Assume single chat window per user (no multi-room support in v1). Handle basic error cases: message send timeout, translation failure (render original), connection loss (indicate to user).

**Acceptance:**
- User A can send a message; it is persisted and translated
- User B receives the translated message in real time (or near-real time if polling)
- Original language and translated content are both stored
- Translation failure does not block message send; original text is rendered with error indicator
- Connection loss is detected and surfaced to the user
- Latency from send to receive is <2s on stable network (target SLO)

**Risk:**

Latency budget depends heavily on translation service latency. If translations take >1s, consider async translation (send original first, update with translation when ready). Tweedle contract negotiation is critical here.
