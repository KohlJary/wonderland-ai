## Test Scenario 001: Rate-limit enforcement — 429 response and Retry-After

**Source:** contract-note-004 (Rate-limit enforcement: 429 response and Retry-After contract)
**Test file:** tests/test_rate_limit_enforcement.py
**Status:** red (tests are written; production code does not exist yet)

### Concern

The rate limiter must enforce quotas reliably and signal rejections in a way that's unambiguous to the client. The server's internal state must be authoritative; clients cannot bypass limits by sending spoofed headers. Retry-After must accurately reflect when the client can retry.

### Scenarios

**Core behavior:**
- Requests within quota (≤10/min) succeed with 200
- Request 11 in the same minute returns 429
- 429 response includes Retry-After header (integer seconds until quota resets)
- 429 response includes JSON body with rate-limit metadata

**Quota isolation:**
- Per-user quota (tracked by User-ID header if present)
- Per-IP fallback quota (for unauthenticated requests)
- Different users have independent buckets
- Quota resets after window closes (1-minute window for 10/min quota)

**Spoofing defense:**
- Client cannot bypass limit by sending X-RateLimit-Remaining or other fake headers
- Server re-derives limits from internal state; client headers are ignored
- Retry-After returned by server is authoritative (not derived from client claims)

**Edge cases:**
- Quota boundary: exactly 10 succeeds, 11 fails
- Multiple rapid requests after quota: all get 429, not sporadic 200s
- 429 rejections don't count toward quota (don't trigger further 429s)
- Invalid messages (validation errors) don't consume quota

### Severity

**critical** — Rate limiting is a defense against abuse. If quotas are not enforced reliably, or if they can be spoofed, the system is vulnerable.

### Coverage

Covered in `TestRateLimitEnforcement` and `TestRateLimitHeaderValidation` classes:
- `test_first_10_requests_succeed` — basic quota
- `test_11th_request_returns_429` — quota boundary
- `test_429_includes_retry_after_header` — header presence
- `test_429_response_body_includes_metadata` — response body
- `test_rate_limit_resets_after_window` — window semantics (property check)
- `test_spoofed_rate_limit_headers_ignored` — spoofing defense
- `test_per_user_quota_with_user_id_header` — per-user isolation
- `test_per_ip_fallback_when_no_user_id` — IP fallback
- `test_multiple_rapid_requests_all_rejected_after_quota` — consistency
- `test_429_does_not_consume_quota` — non-consuming rejections
- `test_server_retry_after_matches_bucket_reset_time` — Retry-After accuracy

### Blockers

None. Tests are ready to run. Production code (rate-limiting middleware) needs to be implemented.

### Notes for Implementation

- Quota window: 1 minute (provisional, tunable via config)
- Quota limit: 10 requests/minute (provisional, tunable via config)
- State store: Redis or DynamoDB (not in-memory; must persist across requests)
- Retry-After format: integer seconds (HTTP standard)
- Spoofing defense: validate User-ID from auth context (not from headers); derive client_ip from X-Forwarded-For with fallback to request.remote_address

### Test Invocations

Run: `pytest tests/test_rate_limit_enforcement.py -v`

Expected: 11 tests, all red (production code not implemented)
