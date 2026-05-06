## Observation 009: Session audit layer deployed; observability hooks incomplete

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T14:45:00Z — 2026-05-05T15:15:00Z

**Symptom:**

Session audit layer (in-memory registry, per-request validation, audit logging) is now operational per the Cat's ADR. Telemetry shows: session creation working (100% success rate on login), audit log writes nominal (0.2ms p95 latency). However, observability instrumentation is incomplete. No metrics on session-store capacity, no alerting on revocation failures, no visibility into whether audit logs are being written to disk before process restart. The Queen's 72-hour breach-investigation deadline depends on audit trail persistence; current implementation has no durability guarantee.

**Affected scope:**

All authenticated requests during and after the credential-stuffing attack window (14:23-15:12 UTC); specifically, session audit trail persistence required for GDPR investigation.

**Evidence:**
- dashboard: session creation success rate 100%, write latency p95 = 0.2ms
- log: 'session audit layer initialized, in-memory store capacity = 10000 sessions'
- code review: http_middleware.py line 145-160 writes to in-memory audit list, no persistent store configured
- audit trail current size: 4,238 session records (attack window + ~15 minutes post-mitigation)

**Probable domain:** backend

**Routed to:** tweedledum
