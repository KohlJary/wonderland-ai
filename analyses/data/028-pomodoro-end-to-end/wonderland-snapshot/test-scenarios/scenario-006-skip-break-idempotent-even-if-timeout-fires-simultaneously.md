## Scenario 006: Skip break idempotent even if timeout fires simultaneously

**Severity:** degradation

**Setup:**

Priya's break has 200ms remaining. She taps Skip. Simultaneously, server timeout fires.

**Trigger:**

Both skip request and timeout within 100ms window.

**Expected:**

Break ends in exactly one final state (skipped or completed), not ambiguous. Idempotent.

**Concern:**

If race not handled, break in inconsistent state. Skip request lost, user waits for timeout.

**Property:**

For all skip requests, if break.remaining_seconds < 1, skip still succeeds and is idempotent.
