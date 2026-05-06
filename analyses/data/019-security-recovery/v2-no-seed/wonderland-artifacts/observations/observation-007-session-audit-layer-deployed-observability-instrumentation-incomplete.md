## Observation 007: Session audit layer deployed; observability instrumentation incomplete

**Type:** post-deploy
**Severity:** sev2
**Time window:** 2026-05-05T15:32:00Z — 2026-05-05T15:47:00Z

**Symptom:**

Tweedledum shipped session_id issuance on successful login (auth_service.py line 154, session_token generated and stored in-memory registry). Audit log format deployed (session_id, endpoint, timestamp tuples written to /var/log/auth_audit.log). No telemetry hooks instrumented: no metrics for session-creation throughput, token-collision rate, cleanup lag, or audit-log write latency. This means: (1) I cannot observe whether session creation is failing under load, (2) Queen's audit-trail parsing for breach investigation will be manual, (3) no alerting if audit logs start dropping due to disk or I/O saturation.

**Affected scope:**

auth_service session layer; audit trail; telemetry gap affecting breach-investigation timeline and Queen's 72-hour deadline

**Evidence:**
- https://github.com/internal/auth_service/pull/4821/files#L154-L168
- logs: tail -f /var/log/auth_audit.log — format is (session_id, endpoint, timestamp), no metric export
- no prometheus metrics found for session_creation_rate, session_collision_errors, audit_log_write_latency

**Probable domain:** backend

**Routed to:** tweedledum
