## Scenario 041: Kohl types a tag but forgets to press Enter, then closes the editor without saving; the tag is lost, but the note itself is in localStorage

**GUID:** 01KRXTAPBP25WMZ6PE0PSWXG6D
**Severity:** degradation

**Setup:**

Kohl has an open editor with title and body. She has typed 'rust' into the TagInput but not pressed Enter or clicked Add. The note's body has unsaved text (covered by the keystroke buffer in localStorage).

**Trigger:**

Kohl closes the browser tab or navigates away without clicking Save.

**Expected:**

The note's title and body are recoverable from localStorage (the keystroke buffer preserves them). The tag 'rust' is not saved anywhere — it was only in the input field, never added to the chips. When Kohl reopens the editor or reloads the page, the body text is restored, but there is no 'rust' tag.

**Concern:**

Kohl typed something she intended to be a tag, but forgot the final keystroke. The loss is acceptable (her mental model is 'I save when I'm ready'), but the degradation is that she has to re-type the tag if she reopens the same note.

**Property:**

Keystroke buffer covers title and body only, not the unsaved input field text in TagInput.

**Implies:**
- The tag input field is NOT persisted to localStorage on each keystroke — only the final chips (after Enter/Add) would be, if we decided to buffer them (we have not for v1).
- This is consistent with the explicit-Save mental model: tags are part of the note state only after Save, not during editing.
