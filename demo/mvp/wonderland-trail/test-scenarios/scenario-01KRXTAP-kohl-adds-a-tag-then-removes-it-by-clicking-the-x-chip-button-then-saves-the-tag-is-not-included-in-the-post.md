## Scenario 042: Kohl adds a tag, then removes it by clicking the X chip button, then saves; the tag is not included in the POST

**GUID:** 01KRXTAPBP25WMZ6PE0PSWXG6E
**Severity:** silent-wrongness

**Setup:**

Kohl has an open editor. Title and body are entered. She has added the tag 'draft' as a chip. The chip shows as a badge with an X button next to it.

**Trigger:**

Kohl clicks the X button on the 'draft' chip. The chip disappears. Then Kohl clicks Save.

**Expected:**

The chip disappears immediately when the X is clicked, and the input field remains focused. The POST /api/notes request body does NOT include 'draft' in tag_names (it is absent, or the array is empty if 'draft' was the only tag). The saved note has no 'draft' tag.

**Concern:**

If the tag is not removed from state when the X is clicked, Kohl's intention to un-tag is not honored, and the tag gets saved anyway. This is a silent failure — the UI shows the chip is gone, but the backend persists it.

**Property:**

Removing a chip from the UI removes it from the tag buffer.

**Implies:**
- The chip's X button has an onClick handler that removes the tag name from the TagInput's state.
- The editor's Save button collects the current state of the tag list, not a cached version.
