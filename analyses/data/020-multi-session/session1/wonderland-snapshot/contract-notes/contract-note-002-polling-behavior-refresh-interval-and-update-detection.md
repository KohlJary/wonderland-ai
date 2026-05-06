## Contract Note 002: Polling behavior: refresh interval and update detection

**State:** agreed
**Contract Version:** polling v1 (2-second interval, full fetch, stop-while-complete optimization, stateless backend)

**Current Shape:**

Skeleton uses synchronous echo; no async or polling pattern yet.

**Proposed Change:**

Frontend polls GET /conversations/{conversation_id}/messages every 2 seconds *only* when the conversation has messages with translation_status = pending_translation. Once all messages are translated or failed, polling stops. Polling resumes if user sends a new message. Each poll is a full fetch of all messages in the conversation (not incremental; simpler for MVP). Backend can optionally include Last-Modified or ETag header to reduce payload on no-change polls, but not required for MVP.

**Source:** ADR-002 polling rationale; ticket-005 scope.

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

No state tracking of polling sessions needed — stateless. Backend must handle polling load: ~2 requests per conversation per 2 seconds, so 500 concurrent active conversations = ~500 requests/sec from polling alone. Index on conversation_id is essential. No cache-busting logic needed; each poll gets current state. If the endpoint becomes a bottleneck, we optimize with conditional requests (Last-Modified) or ETag, but not in v1.

**Resolution:**

AGREED. Contract-note-006 (Tweedledee's perspective) and contract-note-002 (Tweedledum's perspective) describe the same polling load and behavior. Frontend polls GET /conversations/{id}/messages every 2 seconds only while any message has translation_status=pending_translation. Once all messages are translated or failed, polling stops. Resumes when user sends a new message. Backend response is stateless and idempotent. No session tracking, no caching layer required for v1. Polling load: ~500 req/sec at scale, acceptable with conversation_id index + connection pooling. Canonical reference: contract-note-006 with optimization note (stop-while-complete).
