## Contract Note 001: Rate-limit and account-lockout observability events

**State:** proposed
**Contract Version:** (unlocked)

**Current Shape:**

FailedAttempt table logs all failures, but does not distinguish rate-limit/lockout decisions from credential failures. No observable signal is emitted when a rate-limit or lockout threshold is crossed.

**Proposed Change:**

Add three structured event types that observability can subscribe to and instrument: rate_limit_event (IP threshold exceeded), account_lockout_event (email threshold exceeded), successful_login_event (to distinguish attack-window successes from normal logins for breach notification). Each event carries the key (IP / email / user_id), the threshold value crossed, the current count, and a timestamp.

**Source:** Hatter test_scenario slug=rate-limit-decision-fires-but-produces-no-observable-event; Dormouse observation on observability instrumentation gap; Queen's ruling on breach-notification determination requiring observability

**Frontend Impact (Tweedledee):**

Frontend does not emit or consume these events. However, frontend needs to know whether the server will notify users of lockouts, so the contract should specify whether lockout notifications are in-band (immediate response with 'you are locked, contact support') or out-of-band (async email). If out-of-band, frontend needs a separate status-check endpoint to let users verify they're locked. Recommend in-band for this incident response; that's already implemented in endpoints.py (423 Locked response). Out-of-band notification is a fast-follow.

**Backend Impact (Tweedledum):**

TBD — Tweedledum fills in. The question is: does the backend emit these events synchronously in the login flow, or does it write to an audit table and let observability query it? The FailedAttempt table already exists for audit; the choice is whether rate-limit/lockout decisions are also logged there (with a reason field value like 'rate_limited' | 'account_locked') or whether they're emitted as in-process events.
