## Scenario 040: Kohl adds multiple tags to a note over several seconds, then saves; all tags persist

**GUID:** 01KRXTAPBP25WMZ6PE0PSWXG6C
**Severity:** silent-wrongness

**Setup:**

Kohl has an open editor with a partially-written note. Title: 'Protein folding experiment 3'. Body: 'Ran AlphaFold2 on the sequences...' TagInput is visible below the body, focused, and empty.

**Trigger:**

Kohl types 'ml', presses Enter. Types 'protein', presses Enter. Types 'structural-biology', presses Enter. Then clicks Save.

**Expected:**

After each Enter press, a new chip appears below the input (three chips total: 'ml', 'protein', 'structural-biology'). The input field clears after each add and remains focused. When Save is clicked, the POST /api/notes request body includes {tag_names: ['ml', 'protein', 'structural-biology']} (order preserved). The server response includes all three tag_names and their IDs. The editor clears, the chips disappear, and the note is saved with all three tags.

**Concern:**

If any tag is dropped during the sequence, Kohl loses organizational metadata without knowing. If the order is scrambled in the POST, it may affect later sorting or display.

**Property:**

Multiple tags in sequence are all buffered, transmitted, and persisted.

**Implies:**
- TagInput maintains insertion order in its state (use an array or ordered Set, not an unordered object).
- The POST payload preserves the tag order as Kohl entered them.
- The editor collects tags from TagInput in the order they appear in state.
