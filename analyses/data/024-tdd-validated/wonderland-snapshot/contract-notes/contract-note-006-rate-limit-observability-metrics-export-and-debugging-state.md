## Contract Note 006: Rate-limit observability: metrics export and debugging state

**State:** counterpart_assessed
**Contract Version:** (unlocked)

**Current Shape:**

No rate-limit metrics yet.

**Proposed Change:**

Backend emits Prometheus metrics: (1) rate_limit_requests_total (counter, labels: user_id / client_ip, endpoint) — all requests passing through limiter, (2) rate_limit_rejections_total (counter, same labels) — requests rejected with 429, (3) rate_limit_bucket_usage (gauge, labels: user_id / client_ip) — current request count in active bucket. Metrics are updated atomically with rate-limit decision (reject or accept). Per-IP state can be dumped via internal debug endpoint (GET /internal/rate-limit-state) for operator troubleshooting; returns map of {client_id: {requests_in_bucket, bucket_reset_time}}.

**Source:** story-002 (operator observability), ticket-003 (metrics and alerting)

**Frontend Impact (Tweedledee):**

Frontend logs 429 events locally (timestamp, endpoint, retry_available_at derived from header). These logs are available in DevTools or exported if your observability tier requests them. Frontend does not generate rate-limit metrics (that's your domain); I emit the raw events so Dormouse can correlate client perception with server enforcement. User-facing impact: none — this is for debugging, not user experience.

**Backend Impact (Tweedledum):**

Rate limiter exports metrics post-decision. Debug endpoint is internal only (not exposed to unauthenticated clients). Metrics labels include user_id (if authenticated) or client_ip (if not) — frontend does not consume these. No alerting thresholds in v1; operators tune based on dashboards.
