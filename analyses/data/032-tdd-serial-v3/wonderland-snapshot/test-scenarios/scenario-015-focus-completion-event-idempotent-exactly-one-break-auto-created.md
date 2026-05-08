## Scenario 015: Focus completion event idempotent — exactly one break auto-created

**Severity:** silent-wrongness

**Setup:**

Keisha configured break_duration=600s. Focus session ended at 2025-01-15T14:00:00Z.

**Trigger:**

Frontend POSTs /sessions/log with focus completion. Network retry causes identical POST to fire again.

**Expected:**

First POST: 200, focus logged, break auto-created. Second POST: 200 or 409, but NO second break. GET /sessions?date: exactly 1 focus + 1 break.

**Concern:**

Without transaction-level deduplication or idempotency key, retries create phantom sessions. Break auto-start must be part of same transaction as focus-completion, not separate side effect. If decoupled, race condition creates two breaks.

**Property:**

For focus-completion event E POSTed at T and T+delta, backend persists exactly one focus session and exactly one break session. Duplicate events do not create additional sessions.

**Implies:**
- Implies idempotency-key contract must be clarified (separate concern raised).
- Caterpillar should review focus-completion transaction to ensure break auto-start coupling.
