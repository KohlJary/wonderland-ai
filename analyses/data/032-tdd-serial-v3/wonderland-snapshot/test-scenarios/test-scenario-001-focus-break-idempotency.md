## Test Scenario 001: Focus completion event idempotent — exactly one break auto-created

**Severity:** silent-wrongness

**Setup:**

Keisha configured break_duration_seconds=600 (10 min). Her focus session just ended naturally at 2025-01-15T14:00:00Z. The frontend is about to POST the completion event to the backend.

**Trigger:**

The frontend POSTs /sessions/log with:
```json
{
  "type": "focus",
  "duration_configured_seconds": 1500,
  "duration_actual_seconds": 1502,
  "completed_at": "2025-01-15T14:00:00Z"
}
```

The POST receives a response (200, session_id='focus-uuid-1'). Due to network latency or a client-side retry, the IDENTICAL payload is POSTed again 2 seconds later.

**Expected:**

- First POST: 200 OK, focus session logged, break session auto-created with status='running' and duration=600
- Second POST: 200 OK (idempotent response, same session_id) OR 409 Conflict (session already exists), but NO second break created
- GET /sessions?date=2025-01-15: exactly 1 focus session, exactly 1 break session in the response
- GET /daily/summary?date=2025-01-15: break_minutes=10 (600 seconds), not 20

**Concern:**

Without idempotency, network retries create phantom sessions. The backend must deduplicate on either:
- An idempotency key passed in the request header (Stripe-style)
- A natural key (timestamp + type + duration) that's hashed
- A session_id in the payload that's tracked (requires frontend coordination)

The *danger* is that the deduplication logic works for the focus session but NOT for the auto-start logic. Break auto-start might be a side effect that fires independently, creating duplicate breaks even when the focus-completion itself is deduplicated.

**Property:**

For any completed-focus event E = { type: 'focus', duration: D, completed_at: T, ... }, when E is POSTed twice (at time T and T+delta):
- Exactly one focus session with id S_focus is persisted, with session_id returned both times
- Exactly one break session with id S_break is created (not two) on first POST
- Second POST does not create S_break_2
- GET /sessions shows len(focus_sessions) = 1, len(break_sessions) = 1

**Implies:**

This scenario reveals whether the backend's transaction isolation is correct. If auto-start is a separate query/insert, race conditions can create double breaks. Caterpillar should review the focus-completion transaction to ensure auto-start is not a side effect of a separate call.
