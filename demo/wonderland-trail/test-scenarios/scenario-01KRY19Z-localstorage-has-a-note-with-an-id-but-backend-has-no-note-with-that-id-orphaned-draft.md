## Scenario 279: localStorage has a note with an id, but backend has no note with that id (orphaned draft)

**GUID:** 01KRY19Z4NS2MZ90DE1K35D5GK
**Severity:** curiosity

**Setup:**

User created a note, got id=42 from the server, then closed the browser without saving the final version. localStorage has {id: 42, title: 'Final Thoughts', body: '...', ...}. But in a different session, they deleted note 42 from the backend. Now they reload the app. localStorage has the orphaned draft.

**Trigger:**

App boots. Editor or a merge routine tries to fetch GET /notes/42. Backend returns 404 (not found).

**Expected:**

If the draft is newer than the deletion, the user might intend to recreate the note (save it as a new note, or restore from draft). If the draft is older, it's stale and should be discarded. The contract doesn't specify this case. Expected behavior: prompt the user ('Your draft refers to a deleted note. Save as new note? Discard draft?') or log and discard silently (depending on Kohl's preference).

**Concern:**

This is rare (requires a delete in one session and a refresh in another), but it's an edge case the merge logic should handle. Currently, there's no logic to detect 'note with id X exists in localStorage but not in backend.' The Editor component would just try to fetch and fail, leaving the draft in localStorage.

**Property:**

For all notes in localStorage with an id field: on boot, verify that the id exists in the backend. If not, either prompt the user (restore from draft? discard?) or discard silently (per contract). The decision should be explicit, not implicit.

**Implies:**
- Implies contract gap: what's the expected behavior when localStorage has an id that doesn't exist on the backend? Restore as new note? Discard? Show warning?
