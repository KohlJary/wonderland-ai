## Ticket 007: Blocking endpoints (POST/GET/DELETE /blocks with message-send gate)

**Sources:** story: block-a-user-who-is-bothering-me, story: see-my-list-of-blocked-users, story: unblock-someone-and-resume-contact, proposal: user-blocking-additive-model-with-silent-blocking-semantics
**Owner:** tweedledee
**Tier:** v1
**Estimate:** 1–1.5 days, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: blocking-integration-test-suite
- Blocked by: ticket: block-table-schema-and-persistence-layer, ticket: message-send-receive-pipeline-websocket-or-polling-v1
- Soft: ticket: translation-service-integration-api-client-contract

**Description:**

Implement three endpoints: (1) POST /blocks/{user_id} — create block, idempotent on duplicate; (2) GET /blocks — list my blocks, paginated; (3) DELETE /blocks/{user_id} — unblock. Add gate logic to message-send endpoint (POST /messages): before accepting message, query Block table with (from_user_id, to_conversation_user_id); if exists, return 403 'you are blocked by this user'. Message-list endpoint (GET /messages) already filters via JOIN to Block table (per ADR-002). Blocked user sees 200 with empty list, not 404.

**Acceptance:**
- POST /blocks/{user_id} succeeds, returns 201 with block record
- POST /blocks/{user_id} on duplicate returns 200 (idempotent)
- GET /blocks returns paginated list of my blocks
- DELETE /blocks/{user_id} removes block, returns 204
- Message send from blocked user returns 403 with correct error
- Message list from blocked user returns 200 with empty message array
- Unblocking restores visibility of prior messages in conversation

**Risk:**

Gate logic placement: if message-send atomicity with block-state is required (e.g., race condition during unblock), may need transaction wrapping. Scope accordingly if contract negotiation surfaces this.
