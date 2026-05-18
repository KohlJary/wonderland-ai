## Scenario 222: Kohl searches for a term, the excerpt preview in results truncates a long body — the excerpt doesn't break highlighting at truncation boundary

**GUID:** 01KRXYF6YT5H0S2TNKA6KX1HXB
**Severity:** degradation

**Setup:**

Kohl has a note with a 50,000-character body containing 'attention' at position 140 (in the middle of a paragraph). She searches for 'attention'.

**Trigger:**

The search results display an excerpt (first 150 characters) of the note body.

**Expected:**

If the search term 'attention' appears within the first 150 characters of the body, the excerpt contains the highlighted term. If 'attention' appears after position 150, the excerpt does not include it (and is not highlighted). The excerpt ends cleanly (not mid-word) without breaking HTML or markdown formatting. The UI does not show '...' truncation indicator if needed.

**Concern:**

If truncation splits a markdown code block or leaves an unclosed HTML tag, the highlight rendering could break. If highlighting tries to match text outside the excerpt, the DOM might be malformed. Kohl sees garbled display or no highlights where they should be.

**Property:**

Excerpt truncation and highlighting must cooperate: only highlight terms that actually appear in the displayed excerpt.

**Implies:**
- excerpt-truncation-before-highlighting
- no-cross-boundary-highlights
- markdown-integrity-after-truncation
