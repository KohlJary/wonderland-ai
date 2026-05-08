## Scenario 010: Break timer skip is explicit, not accidental (UI intent boundary)

**Severity:** breakage

**Setup:**

Break timer is running (type='break', status='running'). Break session has duration_seconds=300 (5 minutes). User's finger is near the skip button.

**Trigger:**

User double-taps the skip button in rapid succession, or taps skip while button is re-rendering.

**Expected:**

Only ONE skip action is processed. Session transitions to status='completed', completion_type='skip'. Second tap returns 409 Conflict or is silently idempotent (already completed).

**Concern:**

The contract says 'user must tap skip explicitly' but doesn't protect against double-tap or concurrent requests. Mobile especially: race between UI re-render and user's second tap can cause double-skip.

**Property:**

A break session skip operation is idempotent. Processing skip twice yields the same final state as processing it once.
