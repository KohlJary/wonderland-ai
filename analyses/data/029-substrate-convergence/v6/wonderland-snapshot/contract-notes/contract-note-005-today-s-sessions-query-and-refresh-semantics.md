## Contract Note 005: Today's sessions query and refresh semantics

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

undefined

**Proposed Change:**

Define GET /sessions/today that returns array of sessions created on current date (user's timezone). Specify: polling interval (suggest 5s while session active, 30s while idle), or WebSocket event when session completes. Frontend assumes polling unless WS is specified.

**Source:** Feature 003; Ticket 004–005 need this boundary clear.

**Frontend Impact (Tweedledee):**

If polling: implement timer loop; handle stale data gracefully (show 'refreshing' state). If WebSocket: subscribe on mount, unsubscribe on unmount. Either way, list must update automatically after session completion without manual refresh. Offline state: queue mutations, replay on reconnect.

**Backend Impact (Tweedledum):**

GET /sessions/today is fast, no server push needed for v1. Response time should be <100ms (simple query, indexed). Frontend should poll every 5s while session active, 30s while idle. WebSocket is v1.1 — I'd recommend standard SSE (Server-Sent Events) instead if you want push; easier for backend (stateless) and client (reconnect-safe). Offline: client queues mutations in IndexedDB, replays on reconnect. Server accepts replays with same idempotency key (e.g., client-generated request_id) and deduplicates. For v1, mutations are best-effort; we don't retry on client offline yet.
