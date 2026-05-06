## Ticket 007: Implement rate-limit and lockout observability (metrics + events) for breach-notification determination

**Sources:** concern: white-rabbit-observability-debt-for-breach-notification, ruling: breach-notification-obligations-credential-stuffing-success-determination-and-user-notification
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 2-3 hours, 70% confident
**Status:** open

**Dependencies:**
- Blocks: ticket: implement-breach-notification-determination-which-accounts-succeeded-in-attack
- Blocked by: —
- Soft: ticket: implement-per-ip-rate-limiting-on-login-endpoint-per-queens-ruling, ticket: implement-account-lockout-policy-and-user-notification

**Description:**

Dormouse: implement observability layer for rate-limiting and account-lockout events. Queen's ruling (breach-notification) requires knowing which accounts experienced successful login during the attack window. To determine 'success', you need (1) metrics on failed attempts per IP and per email, (2) metrics on successful logins per email during attack window, (3) event logs for rate-limit triggers and lockout triggers (with timestamps, IP, email). Add instrumentation to src/auth/endpoints.py and rate_limit.py (new file). Emit events to production telemetry. Ensure Dormouse can query: 'which emails had successful logins between [attack_start] and [attack_end]?' This is the input to breach-notification work.

**Acceptance:**
- Rate-limit events logged with: timestamp, source IP, failed-attempt count, trigger threshold
- Lockout events logged with: timestamp, email address, failed-attempt count, lockout duration
- Successful login events recorded with: timestamp, email address, source IP, session ID (for audit trail)
- Dormouse can query: 'successful logins for email X during [time window]' with < 1sec latency
- Telemetry dashboard live for: failed attempts per IP, failed attempts per email, lockout count, successful logins

**Risk:**

Observability implementation may create performance overhead if event emission is synchronous. Use async/buffered emission. If telemetry backend is not yet ready, stub the emission and document the dependency.
