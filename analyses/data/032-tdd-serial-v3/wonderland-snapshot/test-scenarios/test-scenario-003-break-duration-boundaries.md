## Test Scenario 003: Break duration boundaries strictly enforced [60, 1800] seconds

**Severity:** degradation

**Setup:**

Per contract-note-006, break_duration_seconds has a range: minimum 60 (1 minute), maximum 1800 (30 minutes). Keisha tries to set invalid values via the settings UI or a direct API call.

**Trigger:**

Test cases attempt to POST /settings (or call the frontend settings function) with:
- Value=0 (zero)
- Value=-10 (negative)
- Value=1 (too small)
- Value=59 (just under minimum)
- Value=1801 (just over maximum)
- Value=7200 (way over)

And also with valid values:
- Value=60, 300, 900, 1800

**Expected:**

For out-of-range values, the backend should:
- EITHER return 400 Bad Request (reject and explain why)
- OR silently clamp to [60, 1800] and return 200 with the clamped value

For valid values:
- Return 200, with the value stored and returned as-is

**Concern:**

If the backend accepts invalid values without clamping, downstream operations will behave unexpectedly. A break with duration=-10 will have negative elapsed time (or wrap to a huge number). A break with duration=0 will "complete immediately" confusing the state machine.

Boundary testing is where many QA teams get lazy — they test 1 value below and 1 value above the boundary, miss the fact that the boundary itself is inclusive or exclusive, and ship off-by-one bugs.

The Hatter tests the boundary *and* the gap — value=59 vs value=60, not just value=1 vs value=100.

**Property:**

For any value V submitted to the break_duration_seconds setting:
- If V ∈ [60, 1800]: accepted as-is, persisted, returned in GET
- If V ∉ [60, 1800]: either rejected (400) or clamped to nearest valid boundary (60 or 1800)

Never silently accept invalid values.

**Implies:**

This tests contract compliance. The Queen might also care about this if there are derived security implications (e.g., a 1-second break configured to spike CPU load). For now, it's a feature boundary test.
