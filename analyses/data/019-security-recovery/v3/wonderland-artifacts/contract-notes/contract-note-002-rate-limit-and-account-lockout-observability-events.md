## Contract Note 002: Rate-limit and account-lockout observability events

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

No observable events emitted from rate-limiting or account-lockout decisions. FailedAttempt table records credentials failures but does not distinguish policy-decision events from authentication failures. HTTP status codes (429, 423) are the only signals; no structured telemetry.

**Proposed Change:**

Emit structured events at decision points: rate-limit-check (when IP-based sliding window check fires), account-locked (when per-email threshold crossed), account-unlocked (when successful login resets counter or manual unlock occurs). Each event carries decision metadata: source_ip, email, threshold/window, timestamp, reason. Events are queryable and aggregatable for both real-time monitoring and post-incident breach-notification determination.

**Source:** Queen ruling #3 (observability required for v1 ship), Caterpillar review (observability absent), Dormouse observations (cannot determine breach scope without instrumentation), Mad Hatter scenarios (monitoring gaps block incident response).

**Frontend Impact (Tweedledee):** _pending_

**Backend Impact (Tweedledum):**

I will add an event-emission layer to rate_limit.py (RateLimiter.check() will emit rate-limit-check event on decision) and auth/service.py (AccountLockout.check() and successful login will emit lockout/unlock events). Events are synchronous and recorded to both a structured log and an in-memory event buffer (for Dormouse to query). The FailedAttempt table remains the audit source; events add real-time visibility. Estimated implementation cost: 4 hours (event schemas, emitters, test coverage). The contract must specify: (1) event types and required fields, (2) cardinality bounds per event type, (3) whether events go to logs, metrics store, or both, (4) retention window for post-incident query.
