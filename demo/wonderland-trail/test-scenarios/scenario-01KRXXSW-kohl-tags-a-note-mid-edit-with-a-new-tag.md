## Scenario 115: Kohl tags a note mid-edit with a new tag

**GUID:** 01KRXXSWWJHYATNJ080FHBB1TH
**Severity:** silent-wrongness

**Setup:**

Kohl has opened an existing note about enzyme kinetics in the editor. The note has a body but no tags yet. The tag input field is visible below the editor.

**Trigger:**

Kohl types 'kinetics' into the tag input, sees it autocomplete to a tag that already exists in the system, selects it, and presses Enter or clicks Add.

**Expected:**

The tag appears as a pill or badge in the note's tag list within the editor. When Kohl saves the note, the tag persists. When Kohl later views the note list, the tag appears alongside the note title.

**Concern:**

If the tag association silently fails (returns 200 but doesn't save), Kohl will re-add the tag repeatedly, assuming it didn't take. If the tag appears in the editor but vanishes on save or reload, Kohl loses trust in the feature.

**Property:**

Tag associations must be durable and immediately reflected in the UI.
