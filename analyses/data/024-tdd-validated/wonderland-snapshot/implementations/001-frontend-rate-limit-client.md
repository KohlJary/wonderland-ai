# Implementation: Frontend rate-limit client

**Tickets:** ticket-002
**Stories:** From three-contract-note proposal (rate-limit-messaging-v1)
**Contract:** Tweedledum's rate-limit-enforcement-v1 (429 + Retry-After header); rate-limit-messaging-v1 (429 body with reason field)

## UI States Implemented

- **allowed**: not rate-limited, user can send requests
- **rate_limited**: countdown active, send button disabled, incoming requests queued
- **error-recoverable**: 429 received, display countdown "Please wait N seconds"
- **pending-sync**: queued requests waiting for window to close

## Client State

RateLimitClient singleton tracks:
1. `status`: "allowed" or "rate_limited" (switches on 429 receipt)
2. `resetTime`: Unix timestamp (ms) when quota resets (derived from Retry-After header + Date.now())
3. `secondsUntilReset`: countdown value for UI display (decremented every 1 second)
4. `queue`: FIFO array of MessageCreate payloads queued while rate-limited

**Reconciliation with server state:** Client does NOT duplicate server's bucket_reset_time. We extract Retry-After header from 429 response, compute local resetTime, and countdown. This avoids clock-skew issues (no assumption that client and server clocks are synchronized). When countdown reaches zero, client marks itself "allowed" and drains queued requests. Server remains authoritative on bucket state.

## Contract Assumptions

1. 429 response always includes `Retry-After` header (integer seconds)
   - If missing, default to 60 seconds (defensive)
   - If malformed, default to 60 seconds (defensive)

2. 429 response body includes at least one of: `reason`, `error`, `message`
   - Used for error message display to user
   - Falls back gracefully if all missing

3. Rate-limit is per-client (User-ID or IP)
   - Client sends User-ID header if authenticated
   - Backend derives client ID from header or X-Forwarded-For or socket IP
   - No client-side awareness of per-client bucketing (server handles it)

## Known Limitations

1. **Queue persistence**: Queued requests are in-memory only. Page refresh clears queue. Persistence to localStorage is deferred.
2. **Countdown granularity**: Updates every 1 second via setInterval. Could optimize to requestAnimationFrame for smoother UI.
3. **Retry strategy**: All queued requests drain at once when window closes. No exponential backoff or jitter. Could add if needed.
4. **Event system**: Uses window.__rateLimitStatusChange callback hook. Real app would use proper event emitter or state management (Redux/Zustand/etc.).

## Files

- `src/frontend/rate_limit.ts`: RateLimitClient class (state machine, countdown, queue)
- `src/frontend/api_client.ts`: ApiClient fetch wrapper with createMessage() respecting rate limits
- `src/frontend/components/RateLimitError.tsx`: React component for error display + countdown
- `src/frontend/hooks/useRateLimit.ts`: useRateLimit React hook for component integration
- `src/frontend/__tests__/rate_limit.test.ts`: Unit tests for RateLimitClient

## Open Question for Tweedledum

Your 429 response sends both `error` and `reason` fields. Can I assume at least one is always present? My code checks `[reason, error, message]` in order and uses the first truthy value. This affects reliability of error message extraction for the UI.
