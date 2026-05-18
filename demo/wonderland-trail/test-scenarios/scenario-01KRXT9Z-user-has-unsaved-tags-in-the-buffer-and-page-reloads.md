## Scenario 030: User has unsaved tags in the buffer and page reloads

**GUID:** 01KRXT9ZVW04FW51CD98MPDCF6
**Severity:** silent-wrongness

**Setup:**

Editor with title, body, and three tags in TagInput (not yet saved). localStorage buffer contains the full note state.

**Trigger:**

User accidentally closes the tab or the page reloads (F5).

**Expected:**

On reload, the editor restores the title and body from localStorage. The TagInput component also restores the three tags from localStorage (or from the editor's restored state). The tag chips re-appear, so the user's work is not lost.

**Concern:**

Tags might not be persisted to localStorage along with title and body, so when the page reloads, tags are lost even though the note text is preserved. This creates confusion: 'where did my tags go?'

**Property:**

For all tag_names T buffered in the editor's localStorage state, the TagInput component must restore T from that buffer on mount, before any API calls.
