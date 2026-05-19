## Scenario 149: Kohl adds a tag to a note via tag input chip interface and sees it persist after save

**GUID:** 01KRXXXAWJHQN8C8PYSGGBXAS1
**Severity:** silent-wrongness

**Setup:**

Kohl is editing a note titled 'Rust concurrency patterns' with body text. The tag input field is empty. No tags are currently associated with the note.

**Trigger:**

Kohl types 'concurrency' into the tag input field, presses Enter, then clicks the Save button.

**Expected:**

The tag 'concurrency' appears as a removable chip below the tag input. After Save completes, the note reloads and the 'concurrency' tag is still visible as a chip. No error message appears.

**Concern:**

If the tag chip persists in the UI but the backend never received it (silent API failure, or the localStorage buffer was cleared before the save request shipped), Kohl will believe her tag was saved when it wasn't. On page reload, the tag vanishes and she loses her organizational intent.

**Property:**

Tag association is atomic with note save: either the tag is sent to the backend and persists, or the save fails and the user sees an error.

**Implies:**
- The tag input must remain disabled or show loading state while the save is in flight, preventing further edits until confirmation.
- On successful save response, the response must include the persisted tags so the UI can reconcile.
- On save failure, the tag must remain in the input/state so the user can retry without re-typing.
