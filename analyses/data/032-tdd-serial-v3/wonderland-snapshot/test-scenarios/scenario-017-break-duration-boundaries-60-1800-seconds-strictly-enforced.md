## Scenario 017: Break duration boundaries [60, 1800] seconds strictly enforced

**Severity:** degradation

**Setup:**

Contract specifies break_duration ∈ [60s, 1800s]. Test attempts invalid: 0, -10, 1, 59, 1801, 7200.

**Trigger:**

POST /settings with out-of-range and valid values.

**Expected:**

Invalid values: rejected (400) or silently clamped to [60, 1800]. Valid values: accepted as-is (200).

**Concern:**

If invalid values accepted, downstream breaks (duration=-10 inverts time logic). Hatter tests boundaries (59 vs 60, 1800 vs 1801) precisely.

**Property:**

For value V: if V ∈ [60, 1800], accept as-is. If V ∉ [60, 1800], reject or clamp. Never silently store invalid.

**Implies:**
- Tests contract compliance on input validation.
- Tweedledee/Tweedledum: clarify validation responsibility. Ideally both frontend and backend.
