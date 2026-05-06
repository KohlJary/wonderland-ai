## Ruling 016: In-memory rate-limit and lockout state must be reconstructible from FailedAttempt audit table across service restarts

**Severity:** high
**Domain:** logging-and-audit
**Source:** concern from Dormouse; ADR proposal from Cheshire Cat

**Citation:**

OWASP A09:2021 Logging and Monitoring Failures. During an incident, if the auth service restarts, the in-memory cache (rate-limit counters, lockout state) is lost. The audit table (FailedAttempt entries) persists. Post-incident analysis, breach-notification determination, and compliance audit must be able to reconstruct the incident state from the audit table. The metrics layer must not depend on in-memory state surviving restarts.

**Finding:**

The ADR acknowledges the acceptable gap: in-memory state is acceptable for SIGv1 because incident response is human-driven and coordinated; service restarts are intentional and rare during active incident response. But the observability contract (which the Dormouse is writing per my prior ruling) depends on this boundary being explicit. If the Dormouse instruments metrics by querying the in-memory cache, those metrics will vanish on restart. If the Dormouse instruments by reading the audit table, the metrics are durable and post-incident analysis is possible.

**Required Remediation:**

The observability contract must specify that rate-limit and lockout events are derived from the FailedAttempt audit table, not the in-memory cache. During normal operation, in-memory caches may be queried for real-time speed. Across restarts, the audit table is the source of truth. The implementation must ensure: (1) FailedAttempt writes are synchronous (not buffered), so the audit table reflects the current state during the incident, and (2) metrics ingest from the audit table with bounded latency (e.g., within 5 seconds), so post-incident analysis has complete visibility.

**Acceptance Criteria:**
- FailedAttempt audit table is written synchronously on every rate-limit or lockout decision
- Dormouse's metrics ingest from the audit table with latency < [threshold] seconds
- Post-incident analysis can reconstruct complete rate-limit and lockout state from the audit table alone, without referencing in-memory cache
- Service restart does not lose audit trail of the incidents that occurred before restart

**Residual Risk:**

There is a narrow window (seconds to minutes after restart) where in-memory state is lost and metrics reconstruction lags. This window is acceptable because: (a) restarts are human-driven during incident response, (b) the attacker can resume at full velocity only if the rate-limit threshold resets, which per-email lockout defeats, and (c) the Dormouse will surface a sev3 observation if audit-to-metrics lag exceeds threshold. The residual risk is monitored and acceptable.

**Compliance Implications:**

Audit trail durability. GDPR Art. 32, HIPAA § 164.312(b), SOC 2 CC6.1. The system must be able to demonstrate, post-incident, that rate limiting and lockout controls were in place and functioning.

**Audit Reference:**

Ruling: In-memory state is acceptable for SIGv1; audit table must be source of truth for observability and post-incident analysis. Dormouse metrics must reconstruct from audit table, with bounded latency.
