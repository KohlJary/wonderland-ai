## Contract Note 006: Polling Contract: GET /conversations/{id}/messages returns all messages with status

**State:** agreed
**Contract Version:** polling v1 (2-second interval, full fetch, stateless, no session tracking)

**Current Shape:**

Skeleton has no polling endpoint. No defined refresh cadence.

**Proposed Change:**

Frontend polls GET /conversations/{id}/messages every 2 seconds (configurable, default 2s). Response is an array of Message objects (schema per contract-note #1). The endpoint is idempotent and includes *all* messages in the conversation, not just new ones. Frontend tracks which messages it has already rendered and only re-renders messages where translation_status has changed or translated_text was populated. Polling stops when user navigates away from conversation. Membership check: caller must be one of the two users in the conversation (400 or 403 if not).

**Source:** adr-002 (polling-based sync); ticket-005 (frontend polling loop); ticket-003 (backend API)

**Frontend Impact (Tweedledee):**

Frontend maintains a Set of rendered message IDs. On each poll response, frontend compares each message's translation_status + translated_text to its local copy. If either changed, re-render that message. This requires local state (a message cache) on the frontend to detect changes. Cache is populated at conversation-open time (full list load) and then updated incrementally via polls. Stale cache could cause missed updates — reconciliation happens at navigation-away time (full re-sync). Polling is the transport; if the team moves to WebSocket later, the response shape and reconciliation logic stay the same.

**Backend Impact (Tweedledum):**

Endpoint is stateless and idempotent. Each call returns current state of all messages in the conversation. No session tracking needed. Polling load: 500 concurrent conversations with active translations = ~500 requests/sec (each conversation polls every 2 seconds, and not all polls happen simultaneously, but peak is bounded). This is acceptable for typical PostgreSQL backend with conversation_id index and connection pooling. No caching layer required for v1; if polling becomes a bottleneck, add ETag support (requires Last-Modified tracking, out of scope for v1). Polling stops when user leaves conversation — the frontend controls the polling cadence, not the backend. Backend responsibility: just answer each query truthfully and fast.

**Resolution:**

Frontend polling loop (maintain cache, detect changes, re-render) is supported by backend endpoint (stateless, idempotent, full fetch, membership check, conversation_id indexing). Polling load is acceptable. Contract is locked.
