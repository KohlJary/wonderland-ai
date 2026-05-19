## Scenario 150: Kohl removes a tag chip from the note via the × button and saves; the tag is removed from the backend

**GUID:** 01KRXXXAWK63FBTGKJSS5NBRY2
**Severity:** silent-wrongness

**Setup:**

Kohl is editing a note that already has two tags: 'rust' and 'concurrency'. Both appear as removable chips in the tag input area.

**Trigger:**

Kohl clicks the × button on the 'concurrency' chip to remove it, then clicks Save.

**Expected:**

The 'concurrency' chip immediately disappears from the UI. After Save completes successfully, the note reloads and only the 'rust' tag is visible. No error message appears.

**Concern:**

If the chip disappears in the UI but the backend never received the removal (silent API failure, or the tag_ids array wasn't updated before save), Kohl will think 'concurrency' is deleted when it's still associated on the server. On page reload, it reappears and her organizational work is undone.

**Property:**

Tag removal is atomic with note save: either the removal is sent to and persisted by the backend, or the save fails and the user sees an error.

**Implies:**
- The tag chip must not disappear from the UI until the save request completes successfully and the response confirms the tag is gone.
- On save failure, the chip must reappear so the user can retry without re-adding it.
- The save payload must include the updated tag_ids array (without the removed tag) so the backend can reconcile.
