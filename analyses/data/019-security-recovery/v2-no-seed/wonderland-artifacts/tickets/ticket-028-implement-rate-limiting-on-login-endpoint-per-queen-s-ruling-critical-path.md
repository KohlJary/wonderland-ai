## Ticket 028: Implement rate-limiting on /login endpoint per Queen's ruling (critical path)

**Sources:** ruling-001, concern-dormouse-incident-observation, ticket-rabbit-implement-rate-limiting-on-login-endpoint-per-queen-ruling
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 45 minutes to 1.5 hours, 65% confident (depends on Cat's architectural clarification on post-login access gating)
**Status:** open

**Dependencies:**
- Blocks: ticket-dormouse-investigate-breach-scope, ticket-tweedledee-display-error-messaging-to-rate-limited-users
- Blocked by: architectural-clarification-cat-access-gating-optional-but-preferred
- Soft: ticket-cheshire-cat-adr-002-session-audit-layer

**Description:**

Deploy rate-limiting middleware on the /login endpoint to halt the ongoing credential-stuffing attack (source IP 203.0.113.42, currently executing 4,127 attempts across 2,803 distinct usernames). Rate-limit shape: 10 login attempts per minute per source IP, with exponential backoff per IP after threshold crossed. Implement rate-limit state in-memory (sufficient for incident response); persistent storage deferred to post-incident hardening. Log all rate-limit events (timestamp, source_ip, username_attempted, success/failure) to audit trail for Dormouse's breach investigation. If Cat clarifies architectural constraint on post-login access gating before implementation begins, incorporate that constraint into the implementation (e.g., if sessions are validated per-request, rate-limit can be simpler; if access is unscoped post-login, rate-limit must be more aggressive). If architectural constraint is not clarified by the time implementation begins, ship rate-limit standalone without incorporating gating (gating becomes a follow-on ticket). Coordinate with Tweedledee on error response contract (what UX does /login return when rate-limited?).

**Acceptance:**
- Rate-limit middleware deployed to /login endpoint and active in production
- /login requests from 203.0.113.42 are rejected with 429 status after 10 attempts/minute
- Audit trail records all rate-limit events (timestamp, source_ip, username, success/failure)
- Dormouse confirms rate-limit logs are flowing and parseable
- Tweedledee confirms error response contract is finalized and ready for UX implementation

**Risk:**

If rate-limit thresholds are too aggressive, collateral legitimate-user lockouts increase (mitigated by unlock flow once deployed). If too lenient, attack continues. Dormouse monitoring will surface the tradeoff in real-time; adjust thresholds within 10 minutes of deployment if necessary. Incident response permits rapid threshold tuning without formal change control.
