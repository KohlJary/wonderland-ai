## Test Scenario 002: Rate-limit messaging — 429 error display and Retry-After countdown

**Source:** contract-note-005 (Rate-limit messaging: 429 error display and Retry-After countdown)
**Test file:** tests/test_rate_limit_messaging.py
**Status:** red (tests are written; backend contracts need validation)

### Concern

The frontend needs to parse 429 responses reliably and display user-friendly error messages with accurate countdowns. The error must be visually distinct from network errors, 5xx errors, auth errors, etc. When users navigate away and return, the countdown resumes from stored state. The error is recoverable (not terminal like 404 or 403).

### Scenarios

**Response parsing:**
- 429 response body is valid JSON (not HTML error page)
- Response includes human-readable reason field (e.g., "Rate limit exceeded")
- Reason clearly identifies rate limit (not cryptic error code)
- Reason is distinguishable from 5xx, auth, validation errors

**Retry-After header:**
- Retry-After is present in all 429 responses
- Retry-After is parseable as integer (seconds)
- Retry-After value is 1–60 seconds (within quota window)
- Multiple 429 responses have consistent Retry-After values

**Error state:**
- 429 is explicitly distinguishable by status_code == 429
- Error state is recoverable (not terminal)
- Error response headers are consistent across multiple 429s
- Message is accessible (WCAG AA contrast, readable type, no color-only indicator)

**User experience:**
- 429 is not confused with network timeout or socket error
- Error message is user-facing (clear language, not "RateLimitExceeded")
- User cannot manually retry until countdown reaches zero
- If user navigates away during window, countdown resumes from stored state

**Edge cases:**
- Invalid messages (validation errors) don't count against quota
- Empty message rejected as 422 (not 429)
- Status code 429 is the hard boundary (not "is this a 4xx?")

### Severity

**high** — Poor error messaging leads users to believe the service is broken, not rate-limited. They may give up, disable the client, or assume their credentials are wrong. Clear messaging is essential to UX.

### Coverage

Covered in `TestRateLimitMessageResponse`, `TestRateLimitRetryAfterParsing`, `TestRateLimitRecoveryAndQueueing`, and `TestRateLimitErrorState` classes:
- `test_429_response_is_json` — JSON format
- `test_429_response_includes_human_readable_reason` — reason field presence
- `test_429_reason_identifies_rate_limit` — reason clarity
- `test_429_response_distinguishable_from_500` — error type distinction
- `test_retry_after_is_integer_seconds` — header parsing
- `test_retry_after_within_quota_window` — value bounds
- `test_rate_limit_is_recoverable_not_terminal` — recovery semantics
- `test_multiple_429s_are_consistent` — consistency across retries
- `test_429_response_status_code_is_explicit` — status code boundary
- `test_429_body_is_always_json` — JSON guarantee
- `test_429_not_confused_with_network_error` — error type distinction
- `test_message_in_429_is_not_cryptic` — user-facing language
- `test_empty_message_not_counted_toward_quota` — quota semantics

### Blockers

None. Tests validate the backend contract that the frontend will depend on.

### Notes for Implementation (Tweedledee)

**Client-side state:**
- Store: `retry_available_at = timestamp_of_429 + Retry_After_value`
- While `retry_available_at > now()`: render "Rate limited until [time]" with countdown
- On `retry_available_at` arrival: drain queued requests

**UI state names:**
- `rate-limited` — user hit quota; UI shows countdown and blocks new requests
- `rate-limited-pending-recovery` — countdown reached zero; awaiting queue drain
- `rate-limited-recovered` — queue drained; normal UI state resumed

**Error handling:**
- Parse response.status_code first (== 429 is the signal)
- If 429: parse Retry-After header → calculate retry_available_at
- Store retry_available_at in persistent client state (survives navigation)
- Queue all outbound requests while rate-limited
- On retry window close: drain queue atomically

### Test Invocations

Run: `pytest tests/test_rate_limit_messaging.py -v`

Expected: 17 tests, all pass (backend contract validation; no production code needed for these)
