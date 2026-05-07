## Scenario 009: Rate-limit metrics are exported; rejections tracked separately from accepts

**Severity:** curiosity

**Setup:**

Backend has Prometheus metrics enabled. Client makes 12 requests (10 accepted, 2 rejected with 429).

**Trigger:**

Metric scrape or /internal/rate-limit-state endpoint query.

**Expected:**

Metrics show: rate_limit_requests_total = 12 (all requests seen), rate_limit_rejections_total = 2 (rejections only). Per-client debugging state shows {client_id: {requests_in_bucket: 10, bucket_reset_time: T}}.

**Concern:**

If metrics are not atomic with rate-limit decision, race conditions cause metrics to diverge from actual behavior (rejections_total could be 1 if update is lost). Without metrics, Dormouse can't detect rate-limit saturation or tune quota. Contract-006 specifies this; it should work correctly so observability is real.

**Property:**

For all time windows W and clients C, rate_limit_requests_total(C, W) = requests_seen(C, W) and rate_limit_rejections_total(C, W) = requests_rejected(C, W).
