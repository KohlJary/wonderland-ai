## Scenario 028: User adds several tags, then saves the note (happy path)

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF4
**Severity:** silent-wrongness

**Setup:**

Editor component is fully rendered (title: 'My experiment', body: 'I tested the new algorithm...', TagInput with three chips: 'algorithm', 'optimization', 'notes'). Save button is visible.

**Trigger:**

User clicks Save button. The editor sends POST /notes with {title, body, tag_names: ['algorithm', 'optimization', 'notes']}. Backend returns 200 with persisted note.

**Expected:**

Tag chip list is cleared after successful save. Input field is empty. Internal state is reset to tag_names: []. If the user starts editing another note, they begin with no tags.

**Concern:**

Tags might not be included in the POST payload, or the tags might not be cleared from the UI after a successful save. Silent wrongness: the user sees tags are still displayed in the UI, but when they reload the page, the tags are gone (backend never persisted them), causing data loss.

**Property:**

For all tag_names T in the component state when Save is clicked, the POST /notes request must include tag_names: T. After a successful save response (2xx), the component must clear tag_names and re-render with an empty chip list.
