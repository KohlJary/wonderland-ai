## Ruling 010: Rate-limit and lockout observability — production telemetry required before v1 ship

**Severity:** high
**Domain:** logging-and-audit
**Source:** test_scenario from Hatter: 'monitoring-gap-rate-limit-and-lockout-events-should-be-observable-in-production'; concern from Dormouse on observability dependencies

**Citation:**

NIST SP 800-61C §5.2.3 (incident detection and analysis via logging); OWASP Logging Cheat Sheet: security events must be logged with sufficient detail to reconstruct attacks and validate controls. Without observable rate-limit events, the next attack cannot be detected early, and the control itself cannot be validated.

**Finding:**

The current implementation of rate-limiting and account lockout will operate without production telemetry. Dormouse will have no visibility into when rate-limiting is triggered, per which dimension (IP, email, endpoint), with what frequency, or whether the controls are actually stopping attacks. This is observability theater: controls that are invisible cannot be trusted or tuned, and the next attack vector will not be detected until it reaches a user-visible failure.

**Required Remediation:**

Before v1 ships, the rate-limiting and account-lockout implementation must emit observable events to production telemetry. Required events: (a) rate-limit-triggered (endpoint, dimension=IP or email, source, timestamp); (b) rate-limit-cleared (same dimensions); (c) account-lockout (email, lockout-reason=failed-login or rate-limit, timestamp); (d) account-unlock (email, unlock-method=timeout or admin, timestamp). These events must be distinct from request logs and aggregatable by dimension (e.g., 'failed logins from IP X in the last hour').

**Acceptance Criteria:**
- Rate-limit and lockout events are emitted to production telemetry (metrics + structured logs)
- Dormouse can query: 'failed logins against email X in the last hour' and see count + source IPs
- Dormouse can query: 'accounts rate-limited in the last hour' and see distribution across endpoints and dimensions
- Hatter's scenario 'monitoring-gap-rate-limit-and-lockout-events-should-be-observable-in-production' passes: Dormouse can construct a timeline of the attack from telemetry alone

**Residual Risk:**

Observable events consume cardinality and storage. If the attacker sends 100k requests/minute, the telemetry volume spikes. Mitigation: cardinality bounds are enforced in the Tweedles' contract note (Dormouse to specify; see prior concern), and archival policy is set so telemetry data does not accumulate indefinitely.

**Compliance Implications:**

GDPR Art. 32 (audit trails); PCI DSS Requirement 10 (logging and monitoring); compliance audits require evidence that security controls are in place and functioning. Observable events are the evidence.

**Audit Reference:**

Threat Garden entry: 'Rate-limiting and lockout controls lack production observability'; ticket dependency for Dormouse to own; must be resolved before v1 release.
