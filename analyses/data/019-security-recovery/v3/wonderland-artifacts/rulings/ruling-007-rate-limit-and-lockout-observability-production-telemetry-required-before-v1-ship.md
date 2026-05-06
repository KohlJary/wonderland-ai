## Ruling 007: Rate-limit and lockout observability — production telemetry required before v1 ship

**Severity:** high
**Domain:** logging-and-audit
**Source:** test_scenario from Mad Hatter (monitoring-gap-rate-limit-and-lockout-events-should-be-observable-in-production)

**Citation:**

OWASP A09:2021 Logging and Monitoring Failures; threat model: without observability of rate-limit and lockout events, the team cannot detect: (a) new attack vectors (distributed IP escalation, password-reset spam); (b) false-positive cascades (legitimate users being locked out in bunches); (c) slow credential-stuffing attacks that evade rate-limit thresholds; (d) whether rate-limiting and lockout are functioning as deployed.

**Finding:**

The current mitigation (per-IP and per-email rate-limiting, account lockout on threshold) produces no observable telemetry. Production will be running blind to: rate-limit events (how many times per minute are thresholds being hit, from which IPs, targeting which emails), lockout events (how many accounts locked, how they were unlocked, patterns in unlock methods), and false-positive patterns (legitimate users being collateral-damaged by the attack). Without this observability, the next attack vector will also go undetected until after user impact.

**Required Remediation:**

Implement structured logging and metrics for: (1) rate-limit-triggered events (timestamp, IP, email, count-at-trigger, threshold, action taken); (2) account-lockout-triggered events (timestamp, email, reason — lockout-threshold-hit vs other, unlock method); (3) rate-limit-cleared events (timestamp, IP/email, clearance reason — time expiry vs password-reset vs admin override). Route to production observability backend (structured logging + metrics). Dormouse to define queries for on-call alerting (e.g., 'alert if unlock-via-reset exceeds N per hour — signals password-reset spam'). This is a v1-blocking dependency for production-safe rate-limiting.

**Acceptance Criteria:**
- Rate-limit events are logged with: timestamp, IP, email, attempt-count, threshold, action-taken
- Account-lockout events are logged with: timestamp, email, reason-code, unlock-method
- Metrics are exported to production observability (Prometheus / equivalent) with dimensions: ip, email, action, reason
- Dormouse has defined at least two on-call queries: (a) 'rate-limit triggers per minute per IP', (b) 'account-lockouts per hour per unlock-method'
- Hatter's scenario 'monitoring-gap-rate-limit-and-lockout-events-should-be-observable-in-production' passes
- Post-deployment: Dormouse confirms telemetry is flowing and queries are actionable within 1 hour of production ship

**Residual Risk:**

Logging at this granularity produces volume; design must balance observability against storage cost. Acceptable: retention of 30 days for rate-limit events, 90 days for lockout events.

**Compliance Implications:**

If breach-notification requirements trigger (see separate ruling), audit logs of rate-limit and lockout events will form part of the incident-response record. Lacking them weakens the defense.

**Audit Reference:**

incident-response thread: observability implementation; post-deployment telemetry validation
