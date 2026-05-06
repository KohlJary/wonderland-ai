## Ticket 019: Implement minimal session audit layer for incident-response visibility

**Sources:** cat-adr-002-session-audit-layer, queen-ruling-002-breach-notification-investigation
**Owner:** tweedledum
**Tier:** v1
**Estimate:** 3-5 hours, 75% confident
**Status:** open

**Dependencies:**
- Blocks: ticket-update-login-lockout-ux-for-already-locked-out-users, ticket-add-unlock-account-cta-to-login-page-for-locked-out-users, ticket-implement-account-recovery-primitive-email-ownership-validation
- Blocked by: —
- Soft: ticket-extend-user-account-lockout-threshold

**Description:**

Add session-token issuance on successful login. Store session ID in in-memory registry with (session_id, user_id, created_at, accessed_endpoints). On each data-access request, validate that session exists and is not revoked. Log (session_id, endpoint, timestamp, http_method) to audit trail for Queen's breach investigation. This is not the final access-gating architecture—it is the minimal primitive that makes audit visibility possible within the incident timeline. Scope: auth_service token generation + in-memory session store + audit logging. Performance optimization and persistent storage are post-incident.

**Acceptance:**
- Session token generated and returned on successful /login
- Session ID stored with user_id and creation timestamp
- Each data-access endpoint logs (session_id, endpoint, timestamp, http_method) to audit trail
- Session revocation removes session from registry; subsequent requests with revoked token are rejected
- Queen can parse audit logs to answer 'what endpoints did session X access?' within 10 minutes

**Risk:**

Session storage correctness under concurrent load, token collision probability, cleanup when sessions expire (in-memory storage will grow without TTL). Mitigate: add 30-minute session TTL and cleanup thread.
