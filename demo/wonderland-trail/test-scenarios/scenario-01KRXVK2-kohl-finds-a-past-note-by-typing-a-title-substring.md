## Scenario 106: Kohl finds a past note by typing a title substring

**GUID:** 01KRXVK28H5RPDTG82TGG11W9P
**Severity:** breakage

**Setup:**

Kohl has created three notes: 'Attention mechanisms in transformers', 'Head attention variants', 'Feedforward layers'. She clicks into the search pane.

**Trigger:**

Kohl types 'attention' into the search input and waits 300ms for the debounce.

**Expected:**

The search results display two notes: 'Attention mechanisms in transformers' and 'Head attention variants' (in any order, or reverse chronological). Each result shows the title, a preview of the body (first 150 characters), any tags, and the creation date. The search pane is visible; the main editor is replaced or minimized.

**Concern:**

If search doesn't work, Kohl can't find her past notes by title — the core use case. If the results are empty or wrong, she thinks the note doesn't exist and re-creates it, losing the original context.

**Property:**

substring match on title
