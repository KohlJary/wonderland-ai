## Scenario 016: Break remaining_seconds never negative — clamping invariant

**Severity:** silent-wrongness

**Setup:**

Break configured 600s. User's clock fast; elapsed_seconds=601 (1s past target).

**Trigger:**

GET /sessions/{break_id} while elapsed > configured (clock drift or scheduler latency).

**Expected:**

remaining_seconds >= 0 (never negative) AND remaining_seconds <= configured. No wrapping to 2^31-1.

**Concern:**

Canary in coal mine. Negative time display shows system doesn't validate invariants. In unsigned ints, -1 wraps to 4,294,967,295. Keisha loses trust in app.

**Property:**

For break B with configured=C and elapsed=E, remaining(B) = max(0, C - E). Always non-negative, bounded by original duration.

**Implies:**
- Tests backend arithmetic safety in session GET endpoint.
- Caterpillar should review GET response calculation for clamping.
