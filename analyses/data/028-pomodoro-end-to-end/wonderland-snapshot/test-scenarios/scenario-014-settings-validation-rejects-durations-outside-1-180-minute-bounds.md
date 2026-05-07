## Scenario 014: Settings validation rejects durations outside [1, 180] minute bounds

**Severity:** degradation

**Setup:**

Dev tries: 0 (invalid), 1 (valid edge), 180 (valid edge), 181 (invalid).

**Trigger:**

Backend validates: 1 <= duration <= 180.

**Expected:**

0 → rejected (400/422). 1 → accepted. 180 → accepted. 181 → rejected.

**Concern:**

If loose, Dev sets invalid durations. System accepts broken input.

**Property:**

For all PATCH /settings, if duration not in [1, 180], server returns 400/422 without updating.
