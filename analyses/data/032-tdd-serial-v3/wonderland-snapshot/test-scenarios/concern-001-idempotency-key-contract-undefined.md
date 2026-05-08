# Concern: POST /sessions/log idempotency mechanism not defined in contract

**Severity:** blocking for M5 implementation

**Issue:**

Contract-note-005 specifies that the frontend will retry `/sessions/log` with exponential backoff, and "backend should treat [the (session_id or timestamp) as idempotent key]." But the contract doesn't define:

1. **What is the idempotency key?** Is it a header (Idempotency-Key: UUID) or derived from the payload (timestamp + type + duration)?
2. **How does the backend detect duplicates?** Hash the payload? Track in a table? TTL on the deduplication store?
3. **What does the backend return on a duplicate?** 200 OK (idempotent) with the original session_id, or 409 Conflict with a reason?

**Why it matters:**

Tweedledum's tests assume idempotency works but don't test the mechanism. When M5 implements the endpoint, the backend engineer won't know:
- Should I add an `idempotency_key` column to the sessions table?
- Should I create a separate idempotency_keys table keyed by (timestamp, type, duration)?
- Should I just reject duplicate (timestamp, type, duration) with 409?

Without this clarity, the implementation will either:
- Ship without idempotency (breaks reoccur, test-scenario-001 fails in production)
- Ship with an ad-hoc idempotency mechanism (Tweedledee and Tweedledum disagree, contract drifts)

**Recommended fix:**

Tweedledum should clarify in contract-note-005: which of these three approaches?

**Option A: Header-based idempotency key (Stripe-style)**
```
POST /sessions/log
Idempotency-Key: <UUID>
{ type: 'focus', ... }
```
Backend tracks recent Idempotency-Key values; duplicate request with same key returns 200 + original session_id.

**Option B: Payload-based natural key (idempotent by design)**
```
POST /sessions/log
{ 
  type: 'focus', 
  duration_configured_seconds: 1500,
  completed_at: '2025-01-15T14:00:00Z',  // <- natural key: (type, duration, timestamp)
  ...
}
```
Backend deduplicates on (type, duration_configured_seconds, completed_at); duplicate is rejected 409 or idempotently returns same session_id.

**Option C: Session_id in payload (frontend-driven idempotency)**
```
POST /sessions/log
{ 
  session_id: 'focus-uuid-1',  // <- client-assigned ID
  type: 'focus',
  ...
}
```
Backend uses the provided session_id; duplicate POST with same session_id is a no-op.

**Recommendation:** Option B (payload-based natural key) is simplest and requires no additional frontend logic. The timestamp + type + duration is already unique enough for this use case.

**Test implication:**

Once the contract is clear, test-scenario-001 (focus_completion_idempotent_duplicate_posts_create_only_one_break) can be refined to test the specific mechanism.
