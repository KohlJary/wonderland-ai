## Ruling 015: Per-email lockout is the primary defense against distributed credential-stuffing; per-IP rate limiting is secondary friction

**Severity:** informational
**Domain:** logging-and-audit
**Source:** proposal from Cheshire Cat; scenario 4 from Mad Hatter

**Citation:**

OWASP A07:2021 Identification and Authentication Failures; threat model: distributed credential-stuffing attack across multiple IPs targeting the same email address. The per-email lockout (5 failed attempts = locked) is the actual defense; the per-IP limit (10 req/min) reduces enumeration efficiency but does not stop distributed attacks.

**Finding:**

The ADR correctly prioritizes per-email lockout as the catch-all defense. Scenario 4 tests the silent-wrongness case: attacker with access to many IPs iterating across them to target a single email address. The per-IP limit does not catch this; the per-email lockout does. The silence risk is that operators or future maintainers might believe the per-IP limit is the primary defense and deprioritize per-email lockout observability. The framing must be explicit in the contract and in the observability signals.

**Required Remediation:**

The implementation must emit observability signals that make the per-email lockout the *primary* signal in production telemetry. Per-IP rate-limit events are secondary. The contract the Dormouse is writing must reflect this priority: per-email lockout events (account locked, account unlocked, unlock method) are high-cardinality; per-IP rate-limit events are informational.

**Acceptance Criteria:**
- Production metrics distinguish per-email lockout events from per-IP rate-limit events with clear naming
- Alerts and dashboards prioritize per-email lockout as the primary threat signal
- Documentation (ADR + runbooks) names per-email lockout as the primary defense and per-IP rate limit as secondary friction

**Residual Risk:**

None. This is a framing ruling, not a blocking one. The code already implements the correct priority; this ruling ensures the observability contract reflects it.

**Audit Reference:**

Ruling: Per-email lockout is primary defense; per-IP rate limit is secondary. Observability contract must reflect this priority.
