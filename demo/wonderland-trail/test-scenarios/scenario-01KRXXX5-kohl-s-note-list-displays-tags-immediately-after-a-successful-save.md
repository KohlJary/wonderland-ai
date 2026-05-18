## Scenario 147: Kohl's note list displays tags immediately after a successful save

**GUID:** 01KRXXX5EYSQXB8M7T8022QXTN
**Severity:** silent-wrongness

**Setup:**

Kohl opens the editor, writes a note 'Experiment Log', adds tags 'attempt-1', 'failed-validation', and clicks Save. The backend responds with HTTP 200 and returns the saved note with all tags. She then navigates to the list view (or the list is already cached and showing).

**Trigger:**

The list view renders the note that was just saved.

**Expected:**

The note 'Experiment Log' appears in the list with both tags displayed as badges. No refresh or re-fetch is required; the tags are visible immediately.

**Concern:**

If the list view doesn't reflect the newly-saved tags (e.g., the tag data is stale or not hydrated from the save response), Kohl will see her note in the list but tags will be missing or incorrect. She loses trust that the save actually persisted.

**Property:**

Tag state in list view must sync with newly-saved note state without requiring explicit refresh.

**Implies:**
- After a successful save (POST /notes or PUT /notes/{id}), the frontend must update the list view's cached note data with the response tags.
- No stale cache or missing cache entries should prevent tags from displaying.
