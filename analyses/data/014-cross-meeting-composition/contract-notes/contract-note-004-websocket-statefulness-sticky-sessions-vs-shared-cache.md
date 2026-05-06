## Contract Note 004: WebSocket Statefulness: Sticky Sessions vs. Shared Cache

**State:** agreed
**Contract Version:** v1 (backend translation service is stateless; each request includes message_id, source_language, target_language; frontend manages client-side cache lifecycle)

**Current Shape:**

Cat's proposal doesn't specify. WebSocket connection handling is frontend's concern per pair protocol, but backend topology (stateful vs. stateless) affects what state the frontend can safely assume persists across reconnects.

**Proposed Change:**

Frontend needs to know: when a WebSocket reconnects (e.g., after a network drop), are subscription state and pending-message state guaranteed to persist on the same backend instance (sticky), or must I assume they might be lost and re-sync from scratch (shared cache)? This determines whether I queue messages client-side during reconnect (sticky assumption = safer to replay) or if I flush and re-request (shared-cache assumption = safer to discard).

**Source:** Tweedledum flagged this as his topology decision, but it's a contract surface because it shapes my reconnection semantics.

**Frontend Impact (Tweedledee):**

WebSocket layer can use either sticky sessions or shared cache for session state—backend translation service doesn't depend on the choice. Tweedledee can choose whichever is simpler for the frontend architecture.

**Backend Impact (Tweedledum):**

Translation service is designed stateless. Each read request is independent; no session affinity required. Scales horizontally without state-replication overhead. Caching is per-instance (in-memory), not shared, so failover causes cache misses but not data loss.

**Resolution:**

agreed—backend stateless, frontend session-scoped cache, no sticky sessions required on either side
