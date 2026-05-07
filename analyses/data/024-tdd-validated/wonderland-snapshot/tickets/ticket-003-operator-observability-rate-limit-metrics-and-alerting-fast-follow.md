## Ticket 003: Operator observability: rate-limit metrics and alerting (fast-follow)

**Sources:** service-operator-understands-rate-limiting-behavior-under-load
**Owner:** tweedledum
**Tier:** fast-follow
**Estimate:** 1.5–2.5 days, 60% confident
**Status:** open

**Dependencies:**
- Blocks: —
- Blocked by: implement-rate-limiting-enforcement-with-header-validation
- Soft: add-user-facing-rate-limit-messaging-and-error-recovery

**Description:**

Emit metrics: request count, quota usage per user, 429-rejection rate, per-user quota utilization percentile. Surface these in the observability stack (Prometheus / Grafana or equivalent) so operators can see rate-limit behavior under load and detect abuse patterns. Do not implement incident response automation in v1 — alerting thresholds are operator-tunable post-launch.

**Acceptance:**
- Rate-limit metrics are exported to observability backend
- Dashboard shows per-user quota utilization and 429-rejection rate
- Operators can distinguish legitimate vs. abusive traffic patterns
- Metrics are queryable by time range and user/IP

**Risk:**

Observability integration point may not be finalized. If the backend doesn't yet have Prometheus emitters, expand to 2.5 days for instrumentation setup.
