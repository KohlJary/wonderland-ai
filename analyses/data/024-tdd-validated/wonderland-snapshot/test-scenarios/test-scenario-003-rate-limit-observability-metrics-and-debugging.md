## Test Scenario 003: Rate-limit observability — metrics export and debugging state

**Source:** contract-note-006 (Rate-limit observability: metrics export and debugging state)
**Test file:** tests/test_rate_limit_observability.py
**Status:** red (tests are written; metrics and debug endpoint not yet implemented)

### Concern

Operators need visibility into rate-limiting behavior under load. Prometheus metrics allow dashboards and alerts; internal debug endpoints help troubleshoot quota issues. State must be exported atomically with rate-limit decisions. Debug endpoints must be access-controlled (internal only).

### Scenarios

**Prometheus metrics:**
- Metrics endpoint exists (e.g., /metrics)
- `rate_limit_requests_total` counter: all requests through limiter
- `rate_limit_rejections_total` counter: requests rejected with 429
- `rate_limit_bucket_usage` gauge: current request count in active bucket
- All metrics labeled by client_id (user_id or client_ip) and endpoint
- Metrics updated atomically with rate-limit decision
- Counters are monotonic (never reset; new buckets start at 0)

**Debug endpoint:**
- GET `/internal/rate-limit-state` returns JSON map of rate-limit state
- State includes per-client-id bucket info: `{client_id: {requests_in_bucket, bucket_reset_time}}`
- Debug endpoint is internal only (not exposed to unauthenticated clients)
- Access control enforced (e.g., special header, internal IP, or 403)
- Different users show separate buckets
- Unauthenticated requests show per-IP buckets

**Observability properties:**
- Frontend logs 429 events locally (timestamp, endpoint, retry_available_at)
- Backend metrics can be correlated with client-side logs
- Operators can identify top rate-limited clients from metrics
- Operators can verify quota window granularity from debug state
- Bucket reset time is visible (helps operators understand window)

### Severity

**medium** — Lack of observability makes operators blind to rate-limiting behavior. They can't verify the limiter is working, can't debug quota issues, can't respond to incidents. Not a user-facing issue, but critical for ops.

### Coverage

Covered in `TestRateLimitMetricsExport`, `TestRateLimitDebugEndpoint`, `TestRateLimitOperatorUseCase` classes:
- `test_metrics_endpoint_exists` — metrics endpoint presence
- `test_rate_limit_requests_total_counter_increments` — requests counter
- `test_rate_limit_rejections_total_counter_increments` — rejections counter
- `test_metrics_include_client_labels` — client labeling
- `test_metrics_include_endpoint_labels` — endpoint labeling
- `test_bucket_usage_gauge_reflects_current_state` — gauge state
- `test_debug_endpoint_exists` — debug endpoint presence
- `test_debug_endpoint_returns_json` — JSON format
- `test_debug_endpoint_shows_client_buckets` — per-client state
- `test_debug_endpoint_shows_requests_in_bucket` — request count visibility
- `test_debug_endpoint_shows_bucket_reset_time` — reset time visibility
- `test_debug_endpoint_access_control` — access control requirement
- `test_debug_endpoint_not_exposed_to_public` — security property
- `test_metrics_updated_atomically_with_rate_limit_decision` — atomicity (property check)
- `test_multiple_rejections_increment_counter` — counter semantics
- `test_metrics_labels_include_http_method` — method labeling (if applicable)
- `test_debug_endpoint_shows_per_ip_buckets` — IP-based buckets
- `test_metrics_survive_bucket_reset` — counter monotonicity
- `test_operator_can_identify_top_rate_limited_clients` — operator use case
- `test_operator_can_see_quota_window_granularity` — debugging aid

### Blockers

None. Tests document the observability contract.

### Notes for Implementation (Tweedledum)

**Prometheus metrics (export on /metrics):**
- Library: prometheus_client (Python standard)
- Counters: `Counter("rate_limit_requests_total", ..., labels=["user_id", "client_ip", "endpoint"])`
- Counters: `Counter("rate_limit_rejections_total", ..., labels=["user_id", "client_ip", "endpoint"])`
- Gauges: `Gauge("rate_limit_bucket_usage", ..., labels=["user_id", "client_ip", "endpoint"])`
- Update: atomic increment in rate-limit middleware, before returning response

**Internal debug endpoint:**
- Route: `GET /internal/rate-limit-state`
- Requires: auth check or internal-IP allowlist (document the mechanism)
- Returns: `{client_id: {requests_in_bucket: int, bucket_reset_at: float_epoch_seconds}}`
- Example:
  ```json
  {
    "user-1": {"requests_in_bucket": 7, "bucket_reset_at": 1699564860},
    "192.168.1.100": {"requests_in_bucket": 3, "bucket_reset_at": 1699564865}
  }
  ```

**Frontend logging (client-side):**
- Log to browser console or local storage: `{timestamp, endpoint, retry_available_at}`
- Include in error reports sent to observability backend (if applicable)
- Does not generate metrics (that's backend's job)

### Test Invocations

Run: `pytest tests/test_rate_limit_observability.py -v`

Expected: 20 tests, mostly red (metrics and debug endpoint not yet implemented)
Skips/xfails acceptable for tests that depend on unimplemented observability.

### Operator Playbook

**Viewing metrics:**
1. Operator navigates to Prometheus dashboard (e.g., Grafana)
2. Panel 1: `rate_limit_rejections_total` by user_id (shows top-rejected clients)
3. Panel 2: `rate_limit_bucket_usage` gauge (shows current bucket fullness)
4. Alert: trigger if `rate_limit_rejections_total` increases by >20 in 5 minutes

**Debugging quota issue:**
1. Operator calls `curl http://internal-api:8000/internal/rate-limit-state` (or internal-IP-restricted)
2. Response shows: `{"user-X": {"requests_in_bucket": 10, "bucket_reset_at": T+60}}`
3. Operator confirms: user hit quota 60 seconds ago, bucket resets in N seconds
4. Operator correlates with user support ticket: "yes, you hit rate limit; retry in N seconds"

### Caveats

- Metrics endpoint location may vary; tests should adapt to your actual path
- Access control mechanism for debug endpoint is deployment-specific; document yours
- Bucket reset time is wall-clock epoch; operator must convert to human time
- Metrics are point-in-time (gauge) or cumulative (counter); understand the distinction
