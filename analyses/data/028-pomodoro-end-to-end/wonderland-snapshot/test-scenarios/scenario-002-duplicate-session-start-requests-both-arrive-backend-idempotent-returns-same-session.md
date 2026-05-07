## Scenario 002: Duplicate /session/start requests both arrive; backend idempotent returns same session

**Severity:** breakage

**Setup:**

Marcus taps Start, network hiccup causes retry. Both requests arrive within 100ms.

**Trigger:**

Backend receives two /session/start requests keyed by (user_id, start_date).

**Expected:**

One session created. Second request returns 200 (or 409) with same session_id. No duplicate active sessions.

**Concern:**

Without idempotency, backend creates two active sessions, violating max-one-active invariant. Or merges requests, corrupting state.

**Property:**

For all user_id, if POST /session/start called twice within 10s with same user context, both return same session_id.
