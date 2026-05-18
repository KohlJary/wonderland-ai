## Scenario 039: Kohl adds a tag to an experimental note, sees it as a chip, saves the note with the tag attached

**GUID:** 01KRXTAPBP25WMZ6PE0PSWXG6B
**Severity:** silent-wrongness

**Setup:**

Kohl opens a new note in the editor. Title field has 'DNA mutation analysis', body field has 'Found unexpected CpG site methylation in control sample.' The tag input is empty and focused.

**Trigger:**

Kohl types 'epigenetics' and presses Enter. The text disappears from the input. Kohl clicks Save.

**Expected:**

The tag 'epigenetics' appears as a removable chip below the input immediately after pressing Enter. The Save button POST request includes {tag_names: ['epigenetics']} in the payload. After the server responds 200, the chip is cleared along with the editor. If Kohl reloads the page and opens the same note, the tag 'epigenetics' is visible in the editor (read-only or editable depending on the note-detail flow).

**Concern:**

If the tag is not included in the POST payload, or if the chip doesn't appear immediately, Kohl will think the tag didn't register and may type it again or abandon the tagging feature. If the tag disappears on save but doesn't persist to the server, Kohl loses the organizational metadata she intended to capture.

**Property:**

Tags are buffered, displayed, and transmitted atomically with the note.

**Implies:**
- The TagInput component maintains a Set<string> of tag names in state.
- The editor's Save button collects tags from TagInput state and includes them in the POST body.
- The POST response includes the persisted tag_names so the editor can confirm the tag was stored.
- On successful save, TagInput clears its buffer.
