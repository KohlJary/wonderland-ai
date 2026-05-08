## Scenario 010: Break timer completion event is idempotent (fires twice, only one session recorded)

**Severity:** silent-wrongness

**Setup:**

Break session is running. Timer has reached 0 and the completion event has fired once (session logged to backend).

**Trigger:**

Due to network retry or event-bus replay, the same completion event fires again (same timestamp, same session ID). Backend receives two POST /sessions/log requests with identical payloads.

**Expected:**

Backend treats the second request as idempotent: it returns 200 OK (or 409 Conflict if the contract allows it), but does NOT create a duplicate session record. Daily history includes the session exactly once.

**Concern:**

If the backend isn't idempotent, the second POST creates a duplicate session. Daily history shows the user worked 50 minutes instead of 25. Analytics are corrupted. This is silent wrongness — the UI looks fine, but the data is wrong. Contracts say frontend will retry with exponential backoff, and idempotency is on the backend to handle duplicates. But contracts don't name the idempotency key or strategy yet.

**Property:**

For any session S with completion event E, if E is delivered twice to POST /sessions/log, the resulting session record in the database is exactly one, not two.

**Implies:**
- Depends on Contract-003 (session completion event) — backend needs to define idempotency. Either: (1) use a session_id + completed_at timestamp as the key, or (2) add an event_id field to the payload.
- This might block M5 if the contract doesn't define the idempotency strategy. Tweedledum: if this is unclear, raise a concern.
