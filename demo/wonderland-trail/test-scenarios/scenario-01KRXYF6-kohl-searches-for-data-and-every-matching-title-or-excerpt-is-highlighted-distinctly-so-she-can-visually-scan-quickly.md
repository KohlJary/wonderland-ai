## Scenario 224: Kohl searches for 'data', and every matching title or excerpt is highlighted distinctly so she can visually scan quickly

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXD
**Severity:** degradation

**Setup:**

Kohl has 5 notes matching 'data'. The word 'data' appears 2–3 times in some of the note excerpts. She needs to quickly scan the results to find the note about 'data analysis'.

**Trigger:**

Search results display with 'data' highlighted in every matching title and excerpt.

**Expected:**

Each instance of 'data' is visibly highlighted (e.g., yellow background, bold text, or distinct color) so Kohl can instantly see why each note matched. The highlight style is consistent across all results and distinct enough to stand out from normal text. Kohl can scan the results in <1 second and find the note she's looking for.

**Concern:**

If highlights are too subtle (same color as body text, no background), Kohl can't quickly spot them and loses the benefit of search. If highlighting is garbled or misaligned (e.g., highlighting the wrong word), Kohl is confused about why a note was returned.

**Property:**

Highlighting must be visually prominent and accurate to enable fast scanning.

**Implies:**
- highlight-color-contrast
- highlight-alignment-with-text
- consistent-highlight-style
- no-misaligned-highlights
