## Test Scenario 002: Break remaining_seconds never goes negative (clamping invariant)

**Severity:** silent-wrongness

**Setup:**

A break session is configured for duration_seconds=600 (10 minutes). The backend calculates remaining_seconds as:

```
remaining_seconds = configured_seconds - elapsed_seconds
```

Keisha's device has a slightly fast clock, or there's scheduler latency. The elapsed_seconds value becomes 601 (1 second past the target).

**Trigger:**

A test or production scenario calls GET /sessions/{break_id} while elapsed_seconds=601 and configured=600.

**Expected:**

The API response includes remaining_seconds, and its value satisfies:
- remaining_seconds >= 0 (never negative)
- remaining_seconds <= configured_seconds (never exceeds the original duration)

**Concern:**

This is the Hatter's signature concern. Negative time is a tell-tale sign that the system doesn't validate its own invariants. It's the canary in the coal mine.

In languages with unsigned integer types (or in JSON, where integers can be arbitrary-precision), an unclamped negative remainder can wrap to:
- 2^31 - 1 (4,294,967,295) if stored as a signed 32-bit int
- 2^63 - 1 if 64-bit
- Or simply -1 if not clamped

When Keisha sees "remaining: 4294967295" or "-1" on her screen, she *loses trust* in the timer. She stops using the app.

The fix is simple: `remaining_seconds = max(0, configured_seconds - elapsed_seconds)`. But without this test, the bug ships.

**Property:**

For any break session B with configured_seconds=C and elapsed_seconds=E (measured at runtime):

remaining_seconds(B) = max(0, C - E)

That is: remaining_seconds is always non-negative and bounded by the original duration.

**Implies:**

This tests the backend's arithmetic safety. Caterpillar should review the session GET endpoint to verify it clamps. The frontend also needs to handle the case where remaining_seconds=0 (timer has finished).
