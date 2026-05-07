## Scenario 015: Partial settings update preserves omitted fields, doesn't reset to default

**Severity:** degradation

**Setup:**

Dev's settings {session: 25, break: 5}. Sends PATCH {session_duration_minutes: 45} (break omitted).

**Trigger:**

Backend processes partial update.

**Expected:**

Result {session: 45, break: 5}. Break unchanged.

**Concern:**

If omitted field resets, Dev loses customization.

**Property:**

For all PATCH /settings, if field omitted, server does not modify that field.
