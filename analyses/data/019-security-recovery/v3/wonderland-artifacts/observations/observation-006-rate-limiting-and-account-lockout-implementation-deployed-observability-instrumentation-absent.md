## Observation 006: Rate-limiting and account-lockout implementation deployed; observability instrumentation absent.

**Type:** incident
**Severity:** sev2
**Time window:** 2026-05-05T15:12:00Z — ongoing

**Symptom:**

Rate-limiting (429) and account-lockout (423) responses are being returned by the auth service in production. No metrics, logs, or events are being emitted to track when these conditions trigger, their frequency, or their targets (IP addresses, email addresses affected). The implementation ships the controls but not the observability required to operate them during an active incident or to determine breach scope post-incident.

**Affected scope:**

Auth service. Rate-limit and lockout events are invisible to production telemetry. Dormouse observability dashboard cannot track attack progression. Queen's breach-notification obligations cannot be fulfilled (no visibility into which login attempts succeeded vs. failed during attack window).

**Evidence:**
- Tweedledee implementation artifact: rate_limit.py contains control logic only; no log statements, no metric hooks, no audit events
- Absence of rate-limit event metrics in Prometheus (checked time range 15:12-present)
- Absence of lockout event logs in production audit stream
- Queen's ruling #3 (observability required before v1 ship) — status: not met

**Probable domain:** backend

**Routed to:** tweedledee
