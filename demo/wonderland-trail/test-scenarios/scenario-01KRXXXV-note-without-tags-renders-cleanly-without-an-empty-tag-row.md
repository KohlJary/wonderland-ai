## Scenario 155: Note without tags renders cleanly without an empty tag row

**GUID:** 01KRXXXVW570ZA3859XC573SKB
**Severity:** degradation

**Setup:**

Search returns three notes: (1) 'Untagged Daily' with tag_names: [], (2) 'Tagged Project' with tag_names: ['work', 'urgent'], (3) 'Another Untagged' with tag_names: []. User performs an empty search to list all notes.

**Trigger:**

All three notes are displayed in the search results list simultaneously.

**Expected:**

Untagged notes display without a tag section and look visually balanced with tagged notes. The spacing and padding around title/preview/date are consistent regardless of whether tags are present. No vertical gap or whitespace is left where a tag section would be.

**Concern:**

If the CSS reserves space for tags (via min-height, margin, or a placeholder div), untagged notes would have excessive whitespace and look misaligned. The renderNoteResult() code checks `note.tag_names.length > 0` before rendering, which is correct, but visual consistency across mixed tagged/untagged lists needs verification.

**Property:**

For all notes N with tag_names.length === 0, the rendered resultItem does not include a visible tag row and has the same visual height as a note with 1-3 tags.
