## Scenario 260: Kohl saves a note in tab A, then quickly makes a new edit and saves again—the second save should detect that the revision_id has changed from the first save's response

**GUID:** 01KRY19NJ0GS53FVHNDWBCBT8B
**Severity:** silent-wrongness

**Setup:**

Kohl saves a note in tab A. The save succeeds, backend returns revision_id 'rev_2'. The frontend updates the local revision_id in component state to 'rev_2'. Kohl then makes a new edit (adds a tag 'networking').

**Trigger:**

Kohl clicks Save again. The frontend sends PUT /notes/{id} with the current state (title, body, tags including 'networking') and revision_id 'rev_2'. The backend processes this and returns revision_id 'rev_3'.

**Expected:**

The second save succeeds (200 response). The UI shows a success message. The local revision_id is updated to 'rev_3' in component state. Both saves persist; the audit trail shows two separate note versions.

**Concern:**

If the frontend doesn't track that the first save already updated revision_id, it may re-use the old revision_id on the second save, which could collide with another tab's write. Or if the frontend clears the localStorage buffer after the first save (violating the 'keystroke buffer is NOT cleared' requirement), the second save's edits would be lost.

**Property:**

The revision_id must be updated in component state immediately after a successful save. The keystroke buffer in localStorage must NOT be cleared after save—only cleared on explicit page reload or Load.

**Implies:**
- Implies that component state must be the source of truth for revision_id, not localStorage.
- Implies that the keystroke buffer persists across multiple save attempts within the same session.
