## Ticket 022: Specify session-telemetry observability hooks required for production incident response

**Sources:** concern from Dormouse on session observability preconditions
**Owner:** Dormouse
**Tier:** v1
**Estimate:** 0.5 days, 85% confident
**Status:** open

**Dependencies:**
- Blocks: implement-minimal-session-audit-layer-for-incident-response-visibility
- Blocked by: —
- Soft: —

**Description:**

Define the observability hooks the Dormouse requires to see the session layer working (or failing) in production. Must include: metrics to detect session-creation failures (token collision, store exhaustion), metrics to detect access-control failures (rejected-request rate on revoked sessions), audit-trail completeness checks (are all requests being logged?), and alerting thresholds that trigger before user harm. This spec gates the Tweedles' instrumentation of the session layer. A session system the Dormouse cannot see is a system that will fail silently.

**Acceptance:**
- Dormouse has published the metrics he will instrument (session creation rate, token collision rate, audit-log write success rate, revoked-token rejection rate)
- Alert thresholds are specified for each metric (e.g., 'alert if token collision rate > 0.1%')
- Log completeness checks are defined (e.g., 'verify all /login requests have corresponding audit records')
- Dormouse confirms he has observability tooling in place to collect these metrics from day one

**Risk:**

If Dormouse waits until after the session layer ships to instrument it, the first few hours of production traffic will be unobservable. Build observability first; instrument as the Tweedles implement.
