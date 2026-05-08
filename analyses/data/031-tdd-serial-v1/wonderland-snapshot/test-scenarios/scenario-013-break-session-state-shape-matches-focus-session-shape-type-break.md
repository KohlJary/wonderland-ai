## Scenario 013: Break session state shape matches focus session shape (type='break')

**Severity:** degradation

**Setup:**

A break session has just been created automatically. System state contains the break session record.

**Trigger:**

Client fetches the active break session via GET /api/sessions/<id>.

**Expected:**

Response includes all fields present in a focus session: session_id, type='break', status, elapsed_ms, duration_seconds, created_at, and all Session model fields. Pause and resume endpoints work identically for break as for focus.

**Concern:**

Contract says 'uses same Session state shape' but doesn't enumerate exact fields. If a field is missing or named differently, pause/resume on a break will fail silently.

**Property:**

Break sessions and focus sessions are indistinguishable in state shape. Only type field differs.
