## Scenario 256: App boots, backend has unsaved note (edge case: note created but never persisted), localStorage is empty

**GUID:** 01KRY19G98KE8SJKZ3Z7K85J7Y
**Severity:** degradation

**Setup:**

Kohl has been using the app, opens it fresh (localStorage cleared by a prior session, or a new device). The backend returns 10 notes. She hasn't opened any note to edit yet.

**Trigger:**

App boots, fetches backend note list.

**Expected:**

App displays the list. No reconciliation is needed — no active editing.

**Concern:**

This is not strictly a reconciliation case (no buffered state), but I want to make sure boot-time note loading doesn't create a scenario where Kohl sees stale data.

**Property:**

On boot, before any user interaction, the backend note list is the source of truth.
