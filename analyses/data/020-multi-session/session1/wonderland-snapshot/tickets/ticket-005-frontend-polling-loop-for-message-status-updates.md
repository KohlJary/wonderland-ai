## Ticket 005: Frontend: Polling loop for message status updates

**Sources:** adr-message-visibility-and-audit-contract-dual-language-display-status-persistence-polling-based-sync
**Owner:** Tweedledee
**Tier:** v1
**Estimate:** 0.5–1 day, 85% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: ticket-003, ticket-004
- Soft: ticket-005

**Description:**

Implement polling loop in conversation view: every 2 seconds, call GET /conversations/{id}/messages and re-render messages with updated translation_status and translated_text. Only re-render messages that changed state (pending → translated or failed). Debounce re-renders if multiple messages update in same poll cycle. Stop polling after user leaves conversation. Log poll latency and error rate for observability.

**Acceptance:**
- Poll interval is 2 seconds (configurable, defaulting to 2s)
- Only messages with changed translation_status are re-rendered
- Polling stops when user navigates away from conversation
- Network errors are logged but don't crash the loop (graceful backoff)
- Poll latency is tracked and exposed as a metric

**Risk:**

If polling latency is high, translation status appears stale. Mitigated by 2s interval. If WebSocket is later chosen, this becomes a transport swap; API contract is unchanged.
