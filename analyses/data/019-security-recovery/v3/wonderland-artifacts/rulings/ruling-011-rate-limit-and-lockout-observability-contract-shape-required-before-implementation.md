## Ruling 011: Rate-limit and lockout observability — contract shape required before implementation

**Severity:** high
**Domain:** logging-and-audit
**Source:** Dormouse concern + Rabbit dependency clarification

**Citation:**

OWASP A09:2021 Logging and Monitoring Failures; SOC 2 CC7.2 (system monitoring and telemetry); incident-response operational requirement: attack patterns are invisible without observability into rate-limit and lockout event distribution

**Finding:**

Rate-limit and lockout events are firing in production but not instrumented for observability. The team cannot detect attack escalations in real-time, cannot debug which attack vector is succeeding, and cannot fulfill post-incident breach-notification obligations without knowing which login attempts succeeded. Shipping rate-limiting without the observability contract that makes it operable is shipping a control you cannot monitor.

**Required Remediation:**

Before the Tweedles resume implementation, the Dormouse will write a rate-limit and lockout observability contract specifying: (1) event types to be observed (rate-limit-triggered, lockout-triggered, unlock-method-used, successful-login-during-attack-window), (2) triggering conditions for each event, (3) per-dimension aggregation (by IP, by email, by timestamp, by User-Agent), (4) cardinality bounds to prevent metric explosion, (5) latency tolerance for event availability in production telemetry (must support real-time SIGv1 response). The contract must distinguish rate-limit events from lockout events from successful authentication events in the telemetry shape, so the Dormouse can read attack patterns correctly.

**Acceptance Criteria:**
- Dormouse contract note exists and specifies event taxonomy, dimensions, and cardinality bounds
- Caterpillar has reviewed the contract note for implementability and telemetry cost
- Tweedles' implementation produces events matching the contract specification
- Dormouse can query production telemetry for successful-login events during attack window within [1 minute] of occurrence
- Dormouse can distinguish rate-limit events, lockout events, and successful-login events in production dashboards without log parsing

**Residual Risk:**

Contract specification cannot account for unforeseen attack patterns. The Dormouse will refine the contract based on real attack data post-incident; observability will be incomplete until refinement is complete. This is acceptable; the goal is functional observability for SIGv1 response, not perfect instrumentation.

**Compliance Implications:**

SOC 2 CC7.2 requires system monitoring of security-relevant events. Rate-limit and lockout events are security-relevant; their absence from telemetry is a control weakness. The contract specification is the artifact that makes this control testable in audit.

**Audit Reference:**

Rate-limit and lockout observability contract; production telemetry event log; Dormouse observability metrics dashboard
