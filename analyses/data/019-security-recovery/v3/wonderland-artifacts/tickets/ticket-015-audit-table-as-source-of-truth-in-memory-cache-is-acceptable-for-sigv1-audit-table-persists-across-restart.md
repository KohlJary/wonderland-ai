## Ticket 015: Audit table as source of truth: in-memory cache is acceptable for SIGv1; audit table persists across restart

**Sources:** ADR: Auth defense-in-depth (in-memory + audit table layering); Dormouse concern about source of truth
**Owner:** Tweedledum
**Tier:** v1
**Estimate:** 0.25–0.5 days, 90% confident
**Status:** open

**Dependencies:**
- Blocks: ticket #8 (observability implementation) — observability must know FailedAttempt is the persistent source
- Blocked by: implementation: rate-limiting and lockout
- Soft: —

**Description:**

The rate-limit and lockout implementation uses in-memory caches (acceptable for incident response) but has no persistence across service restarts. The FailedAttempt audit table is the persistent source of truth. During incident response, when the service restarts, the in-memory cache is lost but the audit table remains. Observability and breach-notification work must reconstruct rate-limit and lockout state from the audit table, not from the in-memory cache. Confirm that FailedAttempt table schema and audit logging are correctly scoped to support breach-notification queries (e.g., 'which accounts had successful login attempts during this time window?'). Output: code review of audit table schema and confirm that the implementation logs both failed and successful attempts with sufficient detail for breach-notification work.

**Acceptance:**
- FailedAttempt table schema includes: timestamp, email, IP, success/failure flag, attempt count at time of log
- Code confirms that successful-login events are logged to FailedAttempt with detail sufficient for breach-notification queries
- Code confirms that in-memory cache and audit table state are consistent at startup (cache is rebuilt from audit table if needed)
- Documentation clarifies the intent: cache for performance, table for durability

**Risk:**

If audit table is incomplete or inconsistent with cache, breach-notification work will be unable to determine which accounts were compromised, violating the Queen's ruling.
