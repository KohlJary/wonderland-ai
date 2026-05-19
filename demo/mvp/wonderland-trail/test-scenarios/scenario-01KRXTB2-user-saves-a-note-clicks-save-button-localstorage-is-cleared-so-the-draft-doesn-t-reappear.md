## Scenario 048: User saves a note (clicks Save button); localStorage is cleared so the draft doesn't reappear

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW6
**Severity:** degradation

**Setup:**

Editor has a draft in localStorage. User clicks the Save button and the note is successfully persisted to the backend (200 response).

**Trigger:**

Save button is clicked. POST /api/notes succeeds.

**Expected:**

After successful save, localStorage['noteDraft'] is cleared (deleted or set to null). The editor's fields are cleared or reset to show the user the save succeeded. If the user reloads the page, the draft is gone and the form is blank (not re-populated with the saved note).

**Concern:**

If localStorage is not wiped after save, the stale draft will reappear on reload, creating confusion about whether the save worked.

**Property:**

After a successful POST to /api/notes, localStorage['noteDraft'] is falsy.

**Implies:**
- Implies a contract: the Save button's success handler must call localStorage.removeItem('noteDraft').
