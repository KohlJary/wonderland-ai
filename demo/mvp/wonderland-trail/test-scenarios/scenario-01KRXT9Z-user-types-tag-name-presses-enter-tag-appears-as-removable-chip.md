## Scenario 022: User types tag name, presses Enter, tag appears as removable chip

**GUID:** 01KRXT9ZVW04FW51CD98MPDCEY
**Severity:** breakage

**Setup:**

TagInput component is rendered in the editor. Text input is focused. No tags have been added yet.

**Trigger:**

User types 'rust' and presses Enter key.

**Expected:**

A chip labeled 'rust' appears below the input field. The input field is cleared and re-focused. The tag is added to the component's internal state (tag_names: ['rust']).

**Concern:**

Enter key might not trigger the add action (key event not wired), or the input might not clear after adding the tag, forcing the user to manually delete the text.

**Property:**

For all tag names T, pressing Enter after typing T into the input should add T to the chip list, clear the input, and re-focus the input (so user can type the next tag without clicking).
