# ADR-002: Message visibility and audit contract: dual-language display, status persistence, polling-based sync

## Context

Alice's three stories surface three observables that the skeleton doesn't support: Klaus needs delivery confirmation (2-3 sec latency); Yuki needs translation fidelity for scientific accuracy (must see original + translation); Sam needs visibility into translation and delivery status for debugging. The Queen's three questions expose that message fidelity, delivery visibility, and real-time sync are not separate concerns—they shape a single data contract and API surface. Translation is inherently async (no third-party service completes in milliseconds), so the message must carry state and persist it. Users will want to know when translation succeeds or fails. Audit will need the trail.

## Decision

1. Message schema stores both original_text (sender's input) and translated_text (peer's view). API responses include both, labeled. Sender sees original; receiver sees translation with attribution.

2. Message has translation_status field (pending_translation | translated | translation_failed). Frontend polls GET /conversations/{id}/messages every 2 seconds to observe status changes. Every status transition is logged with timestamp, error code if applicable. Sam (and audit) can query message logs filtered by status.

3. Real-time delivery for MVP uses polling, not WebSocket. Eventual consistency (2-4 sec latency) over persistent connections. If the team later optimizes to WebSocket, the API contract remains the same.

## Tradeoffs

- Polling adds ~2-4 second latency vs. WebSocket's sub-second. Acceptable for MVP; named for future optimization.
- Dual-text storage increases DB size per message. Mitigated by compression and eventual archival; acceptable for MVP message volume.
- Translation failure visibility to user requires frontend error handling (UX for 'translation failed, showing original'). Essential for confidence; non-negotiable.
- Logging every status transition increases audit trail volume. Acceptable and necessary for compliance; required by Queen's observability need.
- Polling generates API volume. 2-second interval across N conversations = N/2 requests/sec. Scales to ~500 concurrent conversations before hitting typical backend ceiling; acceptable for MVP.

## Status

Proposed
