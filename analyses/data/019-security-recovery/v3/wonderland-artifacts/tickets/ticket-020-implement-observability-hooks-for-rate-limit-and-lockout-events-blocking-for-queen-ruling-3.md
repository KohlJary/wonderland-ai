## Ticket 020: Implement observability hooks for rate-limit and lockout events — blocking for Queen ruling #3

**Sources:** ruling-breach-notification-obligations, ruling-rate-limit-and-lockout-observability-production-telemetry-required-before-v1-ship
**Owner:** Tweedledee / Tweedledum
**Tier:** v1
**Estimate:** 1–2 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: implementation-merge-gate
- Blocked by: dormouse-write-rate-limit-and-lockout-observability-contract-before-implementation
- Soft: —

**Description:**

The Queen ruled 'production telemetry required before v1 ship.' The Dormouse's observability contract (ticket #11) specifies what events must be observable: rate-limit decisions (per IP, per minute), lockout decisions (per email, per threshold), successful logins during attack window, and manual unlock actions. The current implementation does not emit events for any of these. Add instrumentation hooks to src/auth/rate_limit.py and src/auth/service.py such that: (1) every rate-limit check that fires logs/emits a metric 'rate_limit_triggered' with dimensions {ip, timestamp, window_remaining}, (2) every lockout check that fires logs/emits a metric 'account_lockout_triggered' with dimensions {email, timestamp, attempt_count}, (3) every successful login emits an event 'login_success' with dimensions {email, ip, timestamp, prior_lockout_state}, (4) manual unlock actions (when implemented) emit 'account_unlock_manual' with dimensions {email, actor, timestamp}. Do not ship without these hooks; the breach-notification ruling depends on observable login events to determine which accounts to notify.

**Acceptance:**
- Rate-limit trigger events are emitted for every 429 response
- Lockout trigger events are emitted for every 423 response
- Successful login events include timestamp and email (sufficient to query 'logins during attack window')
- Events are queryable/aggregatable by IP, email, timestamp, event type
- Test coverage confirms all four event types fire under the Hatter's six test scenarios

**Risk:**

If Dormouse's contract is incomplete or changes after implementation, the instrumentation may need revision. Lock the contract first.
