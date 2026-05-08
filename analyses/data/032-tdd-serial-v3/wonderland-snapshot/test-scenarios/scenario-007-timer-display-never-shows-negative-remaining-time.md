## Scenario 007: Timer display never shows negative remaining time

**Severity:** silent-wrongness

**Setup:**

Focus session with duration=1500 seconds. Remaining time = duration - elapsed.

**Trigger:**

Due to clock skew or test, elapsed >= 1500, and remaining time calculation would be negative.

**Expected:**

UI displays remaining_time = max(0, duration - elapsed). Never negative, never wraparound.

**Concern:**

If Marcus sees '-1 seconds' or '99:59', he loses trust. Silent wrongness — calculation wrong but only noticed when user looks.

**Property:**

Remaining time to user is clamped to [0, D].

**Implies:**
- Requires careful elapsed-time calculation — contract-001 should clarify how elapsed is measured.
- Requires frontend to clamp display to >= 0.
