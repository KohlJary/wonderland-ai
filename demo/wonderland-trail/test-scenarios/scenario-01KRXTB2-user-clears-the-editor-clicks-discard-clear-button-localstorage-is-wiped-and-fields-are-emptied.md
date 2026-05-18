## Scenario 045: User clears the editor (clicks Discard/Clear button); localStorage is wiped and fields are emptied

**GUID:** 01KRXTB2N1T8SKB4XW9T1D9EW3
**Severity:** breakage

**Setup:**

EditorPane has a draft in localStorage and populated in the fields. A 'Discard Draft' or 'Clear' button is visible.

**Trigger:**

User clicks the Discard/Clear button.

**Expected:**

Both input fields (title and body) are cleared. localStorage['noteDraft'] is deleted or set to null. The editor is now blank and ready for a new draft.

**Concern:**

If the discard action doesn't wipe localStorage, the draft will reappear on next reload, trapping the user in a stale draft state.

**Property:**

After clicking Clear, localStorage['noteDraft'] is empty or falsy, and the input fields contain no text.
