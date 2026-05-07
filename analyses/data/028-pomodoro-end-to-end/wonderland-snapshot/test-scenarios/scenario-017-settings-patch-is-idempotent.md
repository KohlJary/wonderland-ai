## Scenario 017: Settings PATCH is idempotent

**Severity:** degradation

**Setup:**

Dev taps Save on settings form. Request sent, client unsure, retries.

**Trigger:**

Both requests arrive with identical values.

**Expected:**

Both return 200 with identical result. No side effects.

**Concern:**

If not idempotent, retry causes unexpected changes.

**Property:**

For all PATCH /settings with same values sent twice, both return 200 with same result.
