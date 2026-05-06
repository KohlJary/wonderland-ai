## Ticket 010: Dormouse: write rate-limit and lockout observability contract before implementation

**Sources:** concern from Dormouse on observability-specific dependencies
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 2-4 hours, 80% confident
**Status:** open

**Dependencies:**
- Blocks: implement-rate-limit-and-lockout-observability-metrics-events-for-breach-notification-determination
- Blocked by: —
- Soft: confirm-password-reset-endpoint-scope-and-lockout-interaction

**Description:**

Specify the observability contract for rate-limiting and account-lockout events. The contract defines: event types (rate_limit_triggered, rate_limit_cleared, account_locked, account_unlocked), triggering conditions, per-dimension aggregation (per-IP, per-email, per-endpoint where applicable), cardinality bounds, and how these metrics feed breach-notification determination. The contract should be reviewed by Tweedles before implementation so they know what instrumentation 'done' means.

**Acceptance:**
- Contract document specifies event types, triggering conditions, and aggregation dimensions
- Contract identifies per-email vs per-IP metric distinction needed for distributed-IP detection
- Contract specifies cardinality bounds to prevent metric explosion
- Contract reviewed and acknowledged by Tweedles before implementation begins

**Risk:**

If contract is vague about per-email vs per-IP distinction, Tweedles may instrument only per-IP, making distributed-IP attack detection impossible post-incident.
